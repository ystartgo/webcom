# -*- coding: utf-8 -*-
"""
Test suite for High-Precision PCB DXF <-> GeoJSON Converter
Validates:
1. Micro-scale geometry (0.25mm BGA pads, 0.15mm traces, 0402 SMD pads)
2. Bulge arc reconstruction on PCB board outline (90-degree corner fillets)
3. Layer separation (Edge.Cuts, F.Cu, Drill, F.SilkS)
4. Unit auto-detection and scaling (mils -> mm)
5. Full roundtrip: DXF -> GeoJSON -> DXF -> GeoJSON
"""

import os
import sys
import json
import math
import unittest
import tempfile
import ezdxf

# Add scripts and current dir to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pcb_dxf_geojson import PcbDxfGeoJsonConverter, analyze_pcb_dxf, bulge_to_arc_points


class TestPcbDxfGeoJson(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_dxf_path = os.path.join(self.temp_dir, 'synthetic_pcb.dxf')
        self.test_geojson_path = os.path.join(self.temp_dir, 'synthetic_pcb.geojson')
        self.roundtrip_dxf_path = os.path.join(self.temp_dir, 'roundtrip_pcb.dxf')
        self._create_synthetic_pcb_dxf(self.test_dxf_path)

    def _create_synthetic_pcb_dxf(self, filepath: str):
        """
        Creates a realistic micro-scale PCB DXF:
        - Board: 100mm x 60mm with 3mm rounded corner fillets (bulge=tan(pi/8) ~ 0.41421356)
        - Drill: 4x M3 mounting holes (r=1.6mm)
        - F.Cu: 4x4 BGA array (pad r=0.125mm, pitch=0.5mm)
        - F.Cu: SMD 0402 resistor pads (using SOLID)
        - F.Cu: 0.15mm fine trace
        - F.SilkS: Reference designator TEXT
        """
        doc = ezdxf.new('R2010')
        doc.header['$INSUNITS'] = 4  # mm
        msp = doc.modelspace()

        # 1. Edge.Cuts (Board Outline with 4 rounded corners, r=3mm)
        # Bulge for 90 degree arc: b = tan(90 deg / 4) = tan(22.5 deg) = sqrt(2) - 1 ≈ 0.41421356
        b90 = math.tan(math.pi / 8.0)
        # 100x60mm board starting from bottom-left corner with 3mm fillet
        outline_pts = [
            (3.0, 0.0, 0.0),       # Bottom edge start
            (97.0, 0.0, b90),      # Bottom edge end -> corner arc to right edge
            (100.0, 3.0, 0.0),     # Right edge start
            (100.0, 57.0, b90),    # Right edge end -> corner arc to top edge
            (97.0, 60.0, 0.0),     # Top edge start
            (3.0, 60.0, b90),      # Top edge end -> corner arc to left edge
            (0.0, 57.0, 0.0),      # Left edge start
            (0.0, 3.0, b90),       # Left edge end -> corner arc to bottom edge
        ]
        msp.add_lwpolyline(outline_pts, close=True, dxfattribs={'layer': 'Edge.Cuts', 'color': 3})

        # 2. Drill: 4x M3 mounting holes (r=1.6mm)
        for hx, hy in [(5.0, 5.0), (95.0, 5.0), (95.0, 55.0), (5.0, 55.0)]:
            msp.add_circle((hx, hy), radius=1.6, dxfattribs={'layer': 'Drill', 'color': 1})

        # 3. F.Cu: 4x4 High-Density BGA array (pitch 0.5mm, pad diameter 0.25mm / radius 0.125mm)
        bga_center_x, bga_center_y = 50.0, 30.0
        for row in range(4):
            for col in range(4):
                px = bga_center_x + (col - 1.5) * 0.5
                py = bga_center_y + (row - 1.5) * 0.5
                msp.add_circle((px, py), radius=0.125, dxfattribs={'layer': 'F.Cu', 'color': 2})

        # 4. F.Cu: 0402 SMD resistor pads (SOLID: 0.5mm x 0.6mm each, 0.4mm gap)
        # Pad 1
        msp.add_solid([(20.0, 29.7), (20.5, 29.7), (20.0, 30.3), (20.5, 30.3)], dxfattribs={'layer': 'F.Cu', 'color': 2})
        # Pad 2
        msp.add_solid([(20.9, 29.7), (21.4, 29.7), (20.9, 30.3), (21.4, 30.3)], dxfattribs={'layer': 'F.Cu', 'color': 2})

        # 5. F.Cu: Fine 0.15mm trace
        trace_pts = [(21.4, 30.0), (25.0, 30.0), (28.0, 33.0)]
        msp.add_lwpolyline([(p[0], p[1], 0.0) for p in trace_pts], dxfattribs={'layer': 'F.Cu', 'color': 2})

        # 6. F.SilkS: Reference designators
        msp.add_text("U1-BGA16", dxfattribs={'layer': 'F.SilkS', 'color': 7, 'height': 1.2}).set_placement((48.0, 32.0))
        msp.add_text("R1", dxfattribs={'layer': 'F.SilkS', 'color': 7, 'height': 0.8}).set_placement((20.0, 31.0))
        msp.add_text("PCB-DEMO-REV1", dxfattribs={'layer': 'F.SilkS', 'color': 7, 'height': 1.5}).set_placement((10.0, 5.0))

        doc.saveas(filepath)

    def test_dxf_to_geojson_conversion(self):
        """Test reading DXF and parsing into GeoJSON FeatureCollection."""
        converter = PcbDxfGeoJsonConverter(target_unit='mm')
        geojson = converter.dxf_to_geojson(self.test_dxf_path)

        self.assertEqual(geojson['type'], 'FeatureCollection')
        meta = geojson['metadata']
        self.assertEqual(meta['target_unit'], 'mm')
        self.assertEqual(meta['detected_input_unit'], 'millimeters')

        # Verify board dimensions: 100mm x 60mm
        dims = meta['board_dimensions']
        self.assertAlmostEqual(dims['width'], 100.0, places=2)
        self.assertAlmostEqual(dims['height'], 60.0, places=2)
        self.assertAlmostEqual(dims['area_mm2'], 6000.0, places=1)
        self.assertAlmostEqual(dims['area_cm2'], 60.0, places=2)

        # Verify layer breakdown
        layers = meta['layer_breakdown']
        self.assertIn('Edge.Cuts', layers)
        self.assertIn('Drill', layers)
        self.assertIn('F.Cu', layers)
        self.assertIn('F.SilkS', layers)

        # Verify Drill hole count (4 mounting holes)
        self.assertEqual(layers['Drill'], 4)

        # Verify BGA pads (16) + 2 SMD pads + 1 trace in F.Cu = 19
        self.assertEqual(layers['F.Cu'], 19)

    def test_bulge_arc_interpolation(self):
        """Test bulge calculation precision for PCB rounded corners."""
        # 90-degree CCW arc from (97, 0) to (100, 3) with radius = 3mm
        p1 = (97.0, 0.0)
        p2 = (100.0, 3.0)
        bulge = math.tan(math.pi / 8.0)  # 22.5 degrees -> 90 degree central arc
        arc_pts = bulge_to_arc_points(p1, p2, bulge, tolerance=0.005)

        self.assertGreater(len(arc_pts), 8)
        self.assertAlmostEqual(arc_pts[0][0], 97.0, places=4)
        self.assertAlmostEqual(arc_pts[0][1], 0.0, places=4)
        self.assertAlmostEqual(arc_pts[-1][0], 100.0, places=4)
        self.assertAlmostEqual(arc_pts[-1][1], 3.0, places=4)

        # Center should be at (97, 3), radius = 3.0mm
        for pt in arc_pts:
            dist = math.hypot(pt[0] - 97.0, pt[1] - 3.0)
            self.assertAlmostEqual(dist, 3.0, places=3)

    def test_bga_submillimeter_pad_precision(self):
        """Test that sub-millimeter BGA pads (r=0.125mm) retain exact radius and center."""
        converter = PcbDxfGeoJsonConverter(target_unit='mm')
        geojson = converter.dxf_to_geojson(self.test_dxf_path)

        bga_pads = [f for f in geojson['features'] if f['properties'].get('layer') == 'F.Cu' and f['properties'].get('entity_type') == 'CIRCLE']
        self.assertEqual(len(bga_pads), 16)

        for pad in bga_pads:
            props = pad['properties']
            self.assertAlmostEqual(props['radius'], 0.125, places=4)
            self.assertAlmostEqual(props['diameter'], 0.250, places=4)
            self.assertTrue(props['is_pad'])
            self.assertFalse(props['is_drill'])

    def test_mil_to_mm_unit_scaling(self):
        """Test unit scaling when DXF is in mils (thous)."""
        # Create a DXF in mils (1000 mils = 25.4 mm)
        mil_dxf_path = os.path.join(self.temp_dir, 'mil_pcb.dxf')
        doc = ezdxf.new('R2010')
        doc.header['$INSUNITS'] = 9  # mils
        msp = doc.modelspace()
        # 2000 mil x 1000 mil rectangle (50.8 mm x 25.4 mm)
        msp.add_lwpolyline([(0, 0), (2000, 0), (2000, 1000), (0, 1000)], close=True, dxfattribs={'layer': 'Edge.Cuts'})
        doc.saveas(mil_dxf_path)

        converter = PcbDxfGeoJsonConverter(target_unit='mm')
        geojson = converter.dxf_to_geojson(mil_dxf_path)

        dims = geojson['metadata']['board_dimensions']
        self.assertAlmostEqual(dims['width'], 50.8, places=3)
        self.assertAlmostEqual(dims['height'], 25.4, places=3)

    def test_geojson_to_dxf_roundtrip(self):
        """Test roundtrip: DXF -> GeoJSON -> DXF -> GeoJSON."""
        converter = PcbDxfGeoJsonConverter(target_unit='mm')
        original_geojson = converter.dxf_to_geojson(self.test_dxf_path)

        # Write to DXF
        converter.geojson_to_dxf(original_geojson, self.roundtrip_dxf_path)
        self.assertTrue(os.path.exists(self.roundtrip_dxf_path))

        # Re-read the generated DXF
        reloaded_geojson = converter.dxf_to_geojson(self.roundtrip_dxf_path)

        orig_dims = original_geojson['metadata']['board_dimensions']
        reload_dims = reloaded_geojson['metadata']['board_dimensions']

        self.assertAlmostEqual(orig_dims['width'], reload_dims['width'], places=1)
        self.assertAlmostEqual(orig_dims['height'], reload_dims['height'], places=1)

    def test_analyze_pcb_dxf_function(self):
        """Test fast analysis helper."""
        info = analyze_pcb_dxf(self.test_dxf_path)
        self.assertAlmostEqual(info['width_mm'], 100.0, places=2)
        self.assertAlmostEqual(info['height_mm'], 60.0, places=2)
        self.assertEqual(info['total_features'], 27)


if __name__ == '__main__':
    unittest.main()
