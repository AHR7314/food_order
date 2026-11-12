import pathlib
import polib

for po_path in pathlib.Path('locale').rglob('django.po'):
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(po_path.with_suffix('.mo')))
    print('compiled:', po_path)