"""Check relative dependencies, deliverable integrity and OSD source geometry."""
from pathlib import Path
import re, hashlib, json, argparse, zipfile
ROOT=Path(__file__).resolve().parents[1]
NAME='lab_ex3_osd_dsi_SC500_7inch'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-zip',type=Path)
    parser.add_argument('--osd-zip',type=Path)
    args=parser.parse_args()
    projects=[ROOT/'td_project'/f'{NAME}.al',*sorted((ROOT/'td_project'/f'{NAME}_Runs').glob('*/*.prj'))]
    assert len(projects)==3
    checked=0
    for p in projects:
        text=p.read_text(encoding='utf-8-sig')
        for ref in re.findall(r'<File Path="([^"]+)"',text):
            q=(p.parent/ref).resolve()
            assert q.is_file(),str(q)
            assert ROOT in q.parents,str(q)
            checked+=1
        for f in ['dsi_osd_overlay.v','osd_logo_rom.v','osd_char_lib.v']:
            assert text.count('osd/'+f)==1
        assert 'edge_detect_96' not in text
        assert 'hdmi_mixer.v' not in text
        assert 'lab_ex1_mipi_dsi_SC500_7inch_v2' not in text
    print(f'PASS: {len(projects)} TD project/run descriptions; {checked} relative dependencies.')
    logo_file=ROOT/'user_source/hdl_source/osd/anlogic_logo.hex'
    values=[int(v,16) for v in logo_file.read_text().split()]
    assert len(values)==25600 and all(0<=v<(1<<25) for v in values)
    for run in ['syn_1','phy_1']:
        p=ROOT/'td_project'/f'{NAME}_Runs'/run
        assert (p/'../../../user_source/hdl_source/osd/anlogic_logo.hex').resolve()==logo_file
    print('PASS: 25600 valid logo words; synchronous ROM paths resolve from both TD run directories.')
    if args.base_zip:
        n=0
        with zipfile.ZipFile(args.base_zip) as z:
            for name in z.namelist():
                if name.endswith('/'): continue
                rel=name.split('/',1)[1]
                if rel.startswith('user_source/') and rel!='user_source/hdl_source/design_top_wrapper.v':
                    assert (ROOT/rel).read_bytes()==z.read(name),rel
                    n+=1
        print(f'PASS: {n} unchanged example-1 source/IP/constraint files, including ISP, DDR, alignment mixer, panel ROM and DSI.')
    if args.osd_zip:
        pixels=[0]*25600
        with zipfile.ZipFile(args.osd_zip) as z:
            prefix='lab_ex3_osd_SC500_720P/lab_ex3_osd/user_source/hdl_source/'
            original=z.read(prefix+'anlogic_logo_rom.v').decode('utf-8-sig')
            for addr,value in re.findall(r"15'd(\d+): O_pixel = 25'h([0-9a-fA-F]+)",original):
                pixels[int(addr)]=int(value,16)
            assert (ROOT/'user_source/hdl_source/osd/osd_char_lib.v').read_bytes()==z.read(prefix+'osd_char_lib.v')
        actual=[int(x,16) for x in (ROOT/'user_source/hdl_source/osd/anlogic_logo.hex').read_text().split()]
        assert pixels==actual
        print('PASS: all 25600 logo alpha/RGB words and the character library match supplied example 3.')
    m=ROOT/'BUILD_MANIFEST.json'
    if m.exists():
        records=json.loads(m.read_text(encoding='utf8'))['files']
        for item in records: assert sha(ROOT/item['path'])==item['sha256'],item['path']
        print(f'PASS: {len(records)} files match delivery SHA-256 manifest.')

if __name__=='__main__':main()
