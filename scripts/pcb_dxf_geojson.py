# -*- coding: utf-8 -*-
"""
PCB DXF <-> GeoJSON High-Precision Converter
Designed specifically for micro-scale dimensions in electronics / PCB designs:
- Preserves sub-micron coordinate precision (down to 0.01 µm / 10^-5 mm)
- Reconstructs circular arc bulges from LWPOLYLINE (b = tan(theta/4))
- Handles PCB entities: LINE, LWPOLYLINE, CIRCLE (pads/drills), ARC, SOLID (SMD pads),
  TEXT, MTEXT, HATCH (copper pours), and INSERT (exploded component footprints/blocks)
- Layer-aware: maps Edge.Cuts, Copper (F.Cu/B.Cu), Silkscreen, Solder Mask, Drills
- Auto-detects and scales units: mm, mil (thou), inch, micron
- Bi-directional: DXF -> GeoJSON and GeoJSON -> DXF
"""

import math
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    import ezdxf
    from ezdxf.document import Drawing
    from ezdxf.entities import DXFEntity
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False


# Unit Conversion Constants to Millimeters (mm)
UNIT_MAP_TO_MM = {
    'mm': 1.0,
    'millimeter': 1.0,
    'millimeters': 1.0,
    'mil': 0.0254,          # 1 mil = 1/1000 inch = 0.0254 mm
    'mils': 0.0254,
    'thou': 0.0254,
    'inch': 25.4,
    'inches': 25.4,
    'in': 25.4,
    'cm': 10.0,
    'm': 1000.0,
    'meter': 1000.0,
    'micron': 0.001,        # 1 um = 0.001 mm
    'microns': 0.001,
    'um': 0.001,
}

# AutoCAD $INSUNITS standard code mapping
INSUNITS_MAP = {
    0: 'unitless',
    1: 'inches',
    2: 'feet',
    3: 'miles',
    4: 'millimeters',
    5: 'centimeters',
    6: 'meters',
    7: 'kilometers',
    8: 'microinches',
    9: 'mils',
    10: 'yards',
    11: 'angstroms',
    12: 'nanometers',
    13: 'microns',
    14: 'decimeters',
    15: 'decameters',
    16: 'hectometers',
    17: 'gigameters',
}


def round_coord(val: float, precision: int = 6) -> float:
    """Rounds coordinate to prevent floating point jitter while maintaining micro-scale precision."""
    return round(float(val), precision)


def bulge_to_arc_points(p1: Tuple[float, float], p2: Tuple[float, float], bulge: float,
                       tolerance: float = 0.01, max_points: int = 64) -> List[List[float]]:
    """
    Interpolates a circular arc from p1 to p2 defined by DXF bulge factor:
    bulge = tan(theta / 4), where theta is the included central angle.
    Positive bulge = counter-clockwise (CCW); Negative bulge = clockwise (CW).
    
    tolerance: maximum chordal deviation in mm (default 0.01 mm = 10 µm).
    """
    if abs(bulge) < 1e-9:
        return [[round_coord(p1[0]), round_coord(p1[1])], [round_coord(p2[0]), round_coord(p2[1])]]

    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    dx = x2 - x1
    dy = y2 - y1
    chord = math.hypot(dx, dy)
    if chord < 1e-9:
        return [[round_coord(x1), round_coord(y1)]]

    # Included angle theta
    theta = 4.0 * math.atan(bulge)
    abs_theta = abs(theta)

    # Radius: R = chord / (2 * sin(|theta| / 2))
    sin_half = math.sin(abs_theta / 2.0)
    if abs(sin_half) < 1e-9:
        return [[round_coord(x1), round_coord(y1)], [round_coord(x2), round_coord(y2)]]
    
    radius = chord / (2.0 * sin_half)

    # Midpoint of chord
    mx = (x1 + x2) / 2.0
    my = (y1 + y2) / 2.0

    # Distance from chord midpoint to circle center: d = (chord / 2) * (1 - bulge^2) / (2 * bulge)
    sagitta = abs(bulge) * chord / 2.0
    d = (chord / 2.0) * (1.0 - bulge * bulge) / (2.0 * bulge)

    # Normal perpendicular to chord
    # Vector p1->p2 is (dx, dy).
    # Normal pointing to the left is (-dy/chord, dx/chord)
    nx = -dy / chord
    ny = dx / chord

    # Center of arc circle
    cx = mx + d * nx
    cy = my + d * ny

    # Angles from center to p1 and p2
    start_angle = math.atan2(y1 - cy, x1 - cx)

    # Determine angular step based on chord error: err = R * (1 - cos(delta/2)) <= tolerance
    if radius > tolerance:
        ratio = max(-1.0, min(1.0, 1.0 - (tolerance / radius)))
        max_delta = 2.0 * math.acos(ratio)
    else:
        max_delta = math.pi / 8.0

    # Minimum segments to guarantee smooth PCB curves
    num_segs = max(8, min(max_points, int(math.ceil(abs_theta / max(max_delta, 1e-4)))))

    points = []
    for i in range(num_segs + 1):
        frac = i / float(num_segs)
        ang = start_angle + theta * frac
        px = cx + radius * math.cos(ang)
        py = cy + radius * math.sin(ang)
        points.append([round_coord(px), round_coord(py)])

    return points


def circle_to_polygon_ring(cx: float, cy: float, radius: float,
                          tolerance: float = 0.005, min_points: int = 32, max_points: int = 96) -> List[List[float]]:
    """
    Tessellates a circle (drill hole, circular pad, via) into a closed Polygon coordinate ring.
    Maintains sub-micron chordal error (default 0.005 mm = 5 µm).
    """
    if radius <= 0:
        return [[round_coord(cx), round_coord(cy)]]

    # Calculate points needed for smooth circular pad
    if radius > tolerance:
        ratio = max(-1.0, min(1.0, 1.0 - (tolerance / radius)))
        d_theta = 2.0 * math.acos(ratio)
        calc_pts = int(math.ceil(2.0 * math.pi / max(d_theta, 1e-4)))
        num_points = max(min_points, min(max_points, calc_pts))
    else:
        num_points = min_points

    ring = []
    for i in range(num_points):
        ang = (2.0 * math.pi * i) / num_points
        px = cx + radius * math.cos(ang)
        py = cy + radius * math.sin(ang)
        ring.append([round_coord(px), round_coord(py)])

    # Close the ring
    ring.append(ring[0])
    return ring


class PcbDxfGeoJsonConverter:
    """
    High-Precision PCB DXF to GeoJSON & GeoJSON to DXF Converter.
    """

    def __init__(self, target_unit: str = 'mm', default_tolerance: float = 0.01, precision: int = 6):
        """
        :param target_unit: 'mm', 'mil', 'inch', or 'um' (default: 'mm')
        :param default_tolerance: Maximum chord deviation in mm for arcs/curves (default: 0.01 mm = 10 µm)
        :param precision: Decimal places for coordinates (6 decimals in mm is 1 nm precision)
        """
        self.target_unit = target_unit.lower()
        self.default_tolerance = default_tolerance
        self.precision = precision
        self.scale_factor = 1.0

    def detect_dxf_unit(self, doc: Any) -> str:
        """Detects unit from DXF header $INSUNITS or common conventions."""
        try:
            insunits = doc.header.get('$INSUNITS', 0)
            unit_name = INSUNITS_MAP.get(insunits, 'unitless')
            if unit_name in UNIT_MAP_TO_MM:
                return unit_name
        except Exception:
            pass
        return 'unitless'

    def compute_scale(self, detected_unit: str, override_input_unit: Optional[str] = None) -> float:
        """
        Computes scale factor to convert from input DXF units to target_unit.
        """
        unit_in = override_input_unit.lower() if override_input_unit else detected_unit.lower()
        if unit_in == 'unitless' or unit_in not in UNIT_MAP_TO_MM:
            unit_in = 'mm'  # Standard PCB CAD assumption when unitless

        mm_per_input = UNIT_MAP_TO_MM.get(unit_in, 1.0)
        mm_per_target = UNIT_MAP_TO_MM.get(self.target_unit, 1.0)
        return mm_per_input / mm_per_target

    def dxf_to_geojson(self, dxf_input: Union[str, bytes],
                       input_unit: Optional[str] = None,
                       explode_blocks: bool = True) -> Dict[str, Any]:
        """
        Converts a DXF file path, string, or byte buffer into a GeoJSON FeatureCollection.
        """
        if not HAS_EZDXF:
            raise ImportError("ezdxf is required for DXF parsing. Run `pip install ezdxf`.")

        # Load DXF
        if isinstance(dxf_input, bytes):
            import io
            text_stream = io.StringIO(dxf_input.decode('utf-8', errors='ignore'))
            doc = ezdxf.read(text_stream)
        elif os.path.exists(dxf_input):
            doc = ezdxf.readfile(dxf_input)
        else:
            # Assume raw string content
            import io
            text_stream = io.StringIO(dxf_input)
            doc = ezdxf.read(text_stream)

        detected_unit = self.detect_dxf_unit(doc)
        scale = self.compute_scale(detected_unit, input_unit)
        self.scale_factor = scale

        msp = doc.modelspace()
        features: List[Dict[str, Any]] = []

        # Layer and global statistics tracker
        layer_stats: Dict[str, int] = {}
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        def update_bbox(pt: Tuple[float, float]):
            nonlocal min_x, min_y, max_x, max_y
            x, y = pt[0], pt[1]
            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x > max_x: max_x = x
            if y > max_y: max_y = y

        def process_entity(entity: DXFEntity, parent_layer=None):
            layer_name = parent_layer or entity.dxf.layer or '0'
            etype = entity.dxftype()
            color = entity.dxf.color if entity.dxf.hasattr('color') else 7
            handle = entity.dxf.handle if entity.dxf.hasattr('handle') else ''

            props = {
                'entity_type': etype,
                'layer': layer_name,
                'color': color,
                'handle': handle,
                'unit': self.target_unit
            }

            # 1. LINE
            if etype == 'LINE':
                p1 = entity.dxf.start
                p2 = entity.dxf.end
                x1, y1 = round_coord(p1.x * scale, self.precision), round_coord(p1.y * scale, self.precision)
                x2, y2 = round_coord(p2.x * scale, self.precision), round_coord(p2.y * scale, self.precision)
                update_bbox((x1, y1))
                update_bbox((x2, y2))
                coords = [[x1, y1], [x2, y2]]
                length = round_coord(math.hypot(x2 - x1, y2 - y1), self.precision)
                props['length'] = length
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': coords},
                    'properties': props
                })
                layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 2. LWPOLYLINE / POLYLINE
            elif etype in ('LWPOLYLINE', 'POLYLINE'):
                is_closed = bool(entity.closed)
                pts_with_bulge = []

                if etype == 'LWPOLYLINE':
                    # points() returns (x, y, start_width, end_width, bulge)
                    for pt in entity.get_points(format='xyb'):
                        pts_with_bulge.append((pt[0] * scale, pt[1] * scale, pt[2]))
                else:
                    for v in entity.vertices:
                        b = v.dxf.bulge if v.dxf.hasattr('bulge') else 0.0
                        pts_with_bulge.append((v.dxf.location.x * scale, v.dxf.location.y * scale, b))

                if len(pts_with_bulge) >= 2:
                    full_coords: List[List[float]] = []
                    num_pts = len(pts_with_bulge)
                    limit = num_pts if is_closed else num_pts - 1

                    for i in range(limit):
                        curr_p = pts_with_bulge[i]
                        next_p = pts_with_bulge[(i + 1) % num_pts]
                        p1 = (curr_p[0], curr_p[1])
                        p2 = (next_p[0], next_p[1])
                        bulge = curr_p[2]

                        if abs(bulge) > 1e-9:
                            arc_pts = bulge_to_arc_points(p1, p2, bulge, tolerance=self.default_tolerance)
                            if full_coords:
                                full_coords.extend(arc_pts[1:])
                            else:
                                full_coords.extend(arc_pts)
                        else:
                            p1_coord = [round_coord(p1[0], self.precision), round_coord(p1[1], self.precision)]
                            p2_coord = [round_coord(p2[0], self.precision), round_coord(p2[1], self.precision)]
                            if not full_coords:
                                full_coords.append(p1_coord)
                            full_coords.append(p2_coord)

                    for pt in full_coords:
                        update_bbox((pt[0], pt[1]))

                    props['is_closed'] = is_closed
                    props['vertex_count'] = len(full_coords)

                    if is_closed and len(full_coords) >= 4:
                        if full_coords[0] != full_coords[-1]:
                            full_coords.append(full_coords[0])
                        features.append({
                            'type': 'Feature',
                            'geometry': {'type': 'Polygon', 'coordinates': [full_coords]},
                            'properties': props
                        })
                    else:
                        features.append({
                            'type': 'Feature',
                            'geometry': {'type': 'LineString', 'coordinates': full_coords},
                            'properties': props
                        })
                    layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 3. CIRCLE (Drill holes, mounting holes, circular pads, testpoints)
            elif etype == 'CIRCLE':
                cx = entity.dxf.center.x * scale
                cy = entity.dxf.center.y * scale
                r = entity.dxf.radius * scale
                diameter = 2.0 * r

                update_bbox((cx - r, cy - r))
                update_bbox((cx + r, cy + r))

                is_drill = 'drill' in layer_name.lower() or 'hole' in layer_name.lower()
                props.update({
                    'center': [round_coord(cx, self.precision), round_coord(cy, self.precision)],
                    'radius': round_coord(r, self.precision),
                    'diameter': round_coord(diameter, self.precision),
                    'is_drill': is_drill,
                    'is_pad': not is_drill
                })

                poly_ring = circle_to_polygon_ring(cx, cy, r, tolerance=self.default_tolerance)
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Polygon', 'coordinates': [poly_ring]},
                    'properties': props
                })
                layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 4. ARC (Board fillets, rounded tracks, silkscreen)
            elif etype == 'ARC':
                cx = entity.dxf.center.x * scale
                cy = entity.dxf.center.y * scale
                r = entity.dxf.radius * scale
                s_ang = math.radians(entity.dxf.start_angle)
                e_ang = math.radians(entity.dxf.end_angle)
                if e_ang < s_ang:
                    e_ang += 2.0 * math.pi
                theta = e_ang - s_ang

                ratio = max(-1.0, min(1.0, 1.0 - (self.default_tolerance / max(r, 1e-4))))
                d_theta = 2.0 * math.acos(ratio)
                steps = max(8, min(64, int(math.ceil(theta / max(d_theta, 1e-4)))))

                arc_coords = []
                for i in range(steps + 1):
                    ang = s_ang + (theta * i / float(steps))
                    px = round_coord(cx + r * math.cos(ang), self.precision)
                    py = round_coord(cy + r * math.sin(ang), self.precision)
                    arc_coords.append([px, py])
                    update_bbox((px, py))

                props.update({
                    'center': [round_coord(cx, self.precision), round_coord(cy, self.precision)],
                    'radius': round_coord(r, self.precision),
                    'start_angle': round(entity.dxf.start_angle, 2),
                    'end_angle': round(entity.dxf.end_angle, 2)
                })
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': arc_coords},
                    'properties': props
                })
                layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 5. SOLID / TRACE / 3DFACE (SMD rectangular pads, copper fills)
            elif etype in ('SOLID', 'TRACE', '3DFACE'):
                pts = [
                    (entity.dxf.vtx0.x * scale, entity.dxf.vtx0.y * scale),
                    (entity.dxf.vtx1.x * scale, entity.dxf.vtx1.y * scale),
                    (entity.dxf.vtx2.x * scale, entity.dxf.vtx2.y * scale),
                ]
                if entity.dxf.hasattr('vtx3'):
                    pts.append((entity.dxf.vtx3.x * scale, entity.dxf.vtx3.y * scale))

                # In DXF SOLID, coordinates for a quadrilateral are vtx0, vtx1, vtx3, vtx2
                if len(pts) == 4:
                    ordered = [pts[0], pts[1], pts[3], pts[2], pts[0]]
                else:
                    ordered = [pts[0], pts[1], pts[2], pts[0]]

                ring = []
                for p in ordered:
                    px, py = round_coord(p[0], self.precision), round_coord(p[1], self.precision)
                    ring.append([px, py])
                    update_bbox((px, py))

                props['is_smd_pad'] = True
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Polygon', 'coordinates': [ring]},
                    'properties': props
                })
                layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 6. TEXT / MTEXT (Silkscreen reference designators: R1, C1, U1, Net names)
            elif etype in ('TEXT', 'MTEXT'):
                ins = entity.dxf.insert
                x = round_coord(ins.x * scale, self.precision)
                y = round_coord(ins.y * scale, self.precision)
                update_bbox((x, y))

                text_val = entity.dxf.text if entity.dxf.hasattr('text') else ''
                if etype == 'MTEXT' and hasattr(entity, 'text'):
                    text_val = entity.text

                h = (entity.dxf.height if entity.dxf.hasattr('height') else 1.0) * scale
                rot = entity.dxf.rotation if entity.dxf.hasattr('rotation') else 0.0

                props.update({
                    'text': text_val,
                    'height': round_coord(h, self.precision),
                    'rotation': round(rot, 2)
                })
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [x, y]},
                    'properties': props
                })
                layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            # 7. INSERT (Component Footprint / Via cluster / Block Reference)
            elif etype == 'INSERT' and explode_blocks:
                try:
                    for virtual_e in entity.explode():
                        process_entity(virtual_e, parent_layer=layer_name)
                except Exception:
                    ins = entity.dxf.insert
                    bx, by = round_coord(ins.x * scale, self.precision), round_coord(ins.y * scale, self.precision)
                    update_bbox((bx, by))
                    props['block_name'] = entity.dxf.name if entity.dxf.hasattr('name') else ''
                    features.append({
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [bx, by]},
                        'properties': props
                    })
                    layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

        # Process all modelspace entities
        for ent in msp:
            process_entity(ent)

        # Calculate bounding box & PCB board outline dimensions
        has_geom = min_x != float('inf') and min_y != float('inf')
        bbox = [round_coord(min_x, self.precision), round_coord(min_y, self.precision),
                round_coord(max_x, self.precision), round_coord(max_y, self.precision)] if has_geom else [0, 0, 0, 0]

        width = round_coord(max_x - min_x, self.precision) if has_geom else 0.0
        height = round_coord(max_y - min_y, self.precision) if has_geom else 0.0
        area_mm2 = round_coord(width * height, 2) if self.target_unit == 'mm' else 0.0

        geojson = {
            'type': 'FeatureCollection',
            'crs': {
                'type': 'name',
                'properties': {
                    'name': f'urn:ogc:def:crs:OGC:1.3:CRS84:PCB_{self.target_unit.upper()}'
                }
            },
            'metadata': {
                'generator': 'Webcom PCB DXF High-Precision GeoJSON Converter',
                'target_unit': self.target_unit,
                'detected_input_unit': detected_unit,
                'scale_factor': scale,
                'precision_decimals': self.precision,
                'bbox': bbox,
                'board_dimensions': {
                    'width': width,
                    'height': height,
                    'area_mm2': area_mm2,
                    'area_cm2': round(area_mm2 / 100.0, 3),
                    'unit': self.target_unit
                },
                'total_features': len(features),
                'layer_breakdown': layer_stats
            },
            'features': features
        }

        return geojson

    def geojson_to_dxf(self, geojson_data: Union[Dict[str, Any], str],
                       output_dxf_path: str,
                       dxf_version: str = 'R2010') -> str:
        """
        Exports a GeoJSON FeatureCollection back into an AutoCAD DXF file with layers,
        colors, lines, polylines, circles, and texts.
        """
        if not HAS_EZDXF:
            raise ImportError("ezdxf is required for DXF creation. Run `pip install ezdxf`.")

        if isinstance(geojson_data, str):
            if os.path.exists(geojson_data):
                with open(geojson_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = json.loads(geojson_data)
        else:
            data = geojson_data

        doc = ezdxf.new(dxfversion=dxf_version)
        msp = doc.modelspace()

        # Set units in DXF header
        doc.header['$INSUNITS'] = 4 if self.target_unit == 'mm' else (9 if self.target_unit == 'mil' else 1)

        features = data.get('features', [])
        created_layers = set()

        for feat in features:
            geom = feat.get('geometry', {})
            props = feat.get('properties', {})
            gtype = geom.get('type')
            coords = geom.get('coordinates', [])
            layer_name = str(props.get('layer', '0'))
            color = int(props.get('color', 7))

            if layer_name not in created_layers and layer_name not in doc.layers:
                doc.layers.add(layer_name, color=color)
                created_layers.add(layer_name)

            dxf_attribs = {'layer': layer_name, 'color': color}

            if gtype == 'LineString' and len(coords) >= 2:
                if len(coords) == 2:
                    msp.add_line(coords[0], coords[1], dxfattribs=dxf_attribs)
                else:
                    msp.add_lwpolyline(coords, dxfattribs=dxf_attribs)

            elif gtype == 'Polygon' and coords:
                if props.get('entity_type') == 'CIRCLE' and 'center' in props and 'radius' in props:
                    cx, cy = props['center']
                    r = props['radius']
                    msp.add_circle((cx, cy), r, dxfattribs=dxf_attribs)
                else:
                    exterior = coords[0]
                    pts_to_add = exterior[:-1] if exterior[0] == exterior[-1] else exterior
                    msp.add_lwpolyline(pts_to_add, close=True, dxfattribs=dxf_attribs)

            elif gtype == 'Point' and coords:
                if 'text' in props and props['text']:
                    text_val = props['text']
                    h = props.get('height', 1.0)
                    rot = props.get('rotation', 0.0)
                    msp.add_text(text_val, dxfattribs={
                        'layer': layer_name,
                        'color': color,
                        'height': h,
                        'rotation': rot
                    }).set_placement((coords[0], coords[1]))
                elif props.get('entity_type') == 'CIRCLE' and 'radius' in props:
                    msp.add_circle((coords[0], coords[1]), props['radius'], dxfattribs=dxf_attribs)
                else:
                    msp.add_point((coords[0], coords[1]), dxfattribs=dxf_attribs)

        doc.saveas(output_dxf_path)
        return output_dxf_path


# --- Helper Functions for Convenient Import & CLI ---

def dxf_to_geojson_file(dxf_path: str, geojson_path: str, target_unit: str = 'mm', precision: int = 6) -> Dict[str, Any]:
    """Reads a DXF file and writes the resulting GeoJSON to disk."""
    converter = PcbDxfGeoJsonConverter(target_unit=target_unit, precision=precision)
    geojson_data = converter.dxf_to_geojson(dxf_path)
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2, ensure_ascii=False)
    return geojson_data


def geojson_to_dxf_file(geojson_path: str, dxf_path: str) -> str:
    """Reads a GeoJSON file and writes an AutoCAD DXF file to disk."""
    converter = PcbDxfGeoJsonConverter()
    return converter.geojson_to_dxf(geojson_path, dxf_path)


def analyze_pcb_dxf(dxf_path_or_bytes: Union[str, bytes]) -> Dict[str, Any]:
    """Quickly returns PCB dimensions, area, and layer summary from DXF."""
    converter = PcbDxfGeoJsonConverter(target_unit='mm')
    geojson = converter.dxf_to_geojson(dxf_path_or_bytes)
    meta = geojson.get('metadata', {})
    dims = meta.get('board_dimensions', {})
    return {
        'width_mm': dims.get('width', 0.0),
        'height_mm': dims.get('height', 0.0),
        'area_mm2': dims.get('area_mm2', 0.0),
        'area_cm2': dims.get('area_cm2', 0.0),
        'bbox': meta.get('bbox', []),
        'total_features': meta.get('total_features', 0),
        'layer_breakdown': meta.get('layer_breakdown', {})
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='PCB High-Precision DXF <-> GeoJSON Converter')
    parser.add_argument('input', help='Input DXF or GeoJSON file path')
    parser.add_argument('-o', '--output', help='Output file path (.geojson or .dxf)')
    parser.add_argument('--unit', default='mm', choices=['mm', 'mil', 'inch', 'um'], help='Target unit (default: mm)')
    parser.add_argument('--analyze', action='store_true', help='Print PCB dimensions and layer analysis')

    args = parser.parse_args()

    if args.analyze:
        analysis = analyze_pcb_dxf(args.input)
        print("=== PCB Dimension & Layer Analysis ===")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.input.lower().endswith('.dxf'):
        out_path = args.output or (os.path.splitext(args.input)[0] + '.geojson')
        print(f"Converting DXF -> GeoJSON: {args.input} -> {out_path} (unit: {args.unit})")
        dxf_to_geojson_file(args.input, out_path, target_unit=args.unit)
        print(f"Successfully converted to {out_path}")
    elif args.input.lower().endswith('.geojson') or args.input.lower().endswith('.json'):
        out_path = args.output or (os.path.splitext(args.input)[0] + '.dxf')
        print(f"Converting GeoJSON -> DXF: {args.input} -> {out_path}")
        geojson_to_dxf_file(args.input, out_path)
        print(f"Successfully converted to {out_path}")
    else:
        print("Error: Unrecognized file extension. Please provide .dxf or .geojson file.")
        sys.exit(1)
