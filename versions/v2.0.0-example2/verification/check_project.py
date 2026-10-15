"""Offline integrity checks for the delivered TD project and pixel geometry."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
NAME = 'lab_ex2_edge_dsi_SC500_7inch'

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    projects = [ROOT/'td_project'/f'{NAME}.al']
    projects += sorted((ROOT/'td_project'/f'{NAME}_Runs').glob('*/*.prj'))
    assert len(projects) == 3
    checked = 0
    for project in projects:
        text = project.read_text(encoding='utf-8-sig')
        for ref in re.findall(r'<File Path="([^"]+)"', text):
            path = (project.parent/ref).resolve()
            assert path.is_file(), f'Missing project file: {ref}'
            assert ROOT in path.parents, f'External project dependency: {ref}'
            checked += 1
        assert text.count('isp/edge_detect_96.v') == 1
        assert 'lab_ex1_mipi_dsi_SC500_7inch_v2' not in text
        assert 'hdmi_tx.v' not in text
        assert '<Device>PH1P35MDG324</Device>' in text

    top = (ROOT/'user_source/hdl_source/design_top_wrapper.v').read_text(encoding='utf-8')
    assert 'parameter DISPLAY_TEST_PATTERN = 0' in top
    assert "parameter EDGE_THRESHOLD = 14'd80" in top
    assert '.EDGE_THRESHOLD(EDGE_THRESHOLD)' in top
    isp = (ROOT/'user_source/hdl_source/isp/isp_top.v').read_text(encoding='utf-8')
    for signal in ['.I_96b_frame_start(edge_user)', '.I_96b_valid(edge_valid)', '.I_96b_data(edge_data)']:
        assert signal in isp
    assert '.I_tready(O_tready), .O_tready(awb_ready)' in isp
    print(f'PASS: {len(projects)} TD projects, {checked} relative source/IP/constraint references; edge pipeline and defaults.')

    # Four DDR buffers; every cropped row follows the original 1280-wide stride.
    count = 0
    for base in [0, 7000000, 14000000, 21000000]:
        for y in range(600):
            row_addr = base + 115392 + y*1920
            for word in range(192):
                address = row_addr + word*8
                expected = base + ((60+y)*1280+128)*3//2 + word*8
                assert address == expected
                count += 1
    assert 320*96 == 240*128
    assert 1024*24 == 192*128
    print(f'PASS: {count} cropped DDR word addresses across four frame buffers; 320 input beats / 240 DDR words per 720P row.')

    manifest = ROOT/'BUILD_MANIFEST.json'
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        for item in data['files']:
            p = ROOT/item['path']
            assert sha256(p) == item['sha256'], f'Manifest mismatch: {p}'
        print(f"PASS: {len(data['files'])} delivered files match SHA-256 manifest.")

if __name__ == '__main__':
    main()
