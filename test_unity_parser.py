from unitypackage_importer.modules.unitypackage_parser import UnitypackageParser
from unitypackage_importer.modules.logging import get_logger
from unitypackage_importer.modules.tools import timer
import sys

logger = get_logger("Parser Test", True)

# test_file = "D:/#Google Sync/_Assets/_Avatars/Awtter [@ShadeTheBat]/20230720 ShadeDoes3D Products/Awttpack/Awttpack Unity/Awttpack_2.9.75j.unitypackage"
test_file = "D:/#Google Sync/_Assets/_Avatars/Awtter [@ShadeTheBat]/20230720 ShadeDoes3D Products/Base - Awtter/The Awtter/Awtter_3.0.74i_AnNS8nB.unitypackage"

# Create parser
parser = UnitypackageParser(test_file)

# Get some data out of it!
@timer(logger)
def get_all_images():
    for pathname, asset in parser.get_assets_by_extension('.png'):
        # logger.info(f"File: '{pathname}', Bytes: {sys.getsizeof(asset.read())}")
        asset.read()

get_all_images()