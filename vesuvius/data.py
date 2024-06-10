from pathlib import Path

import bpy
import os
import requests
import threading
from requests.auth import HTTPBasicAuth


DATA_URL = "http://dl.ash2txt.org"


def get_data_dir():
	d = bpy.context.preferences.addons["vesuvius"].preferences.data_dir
	return Path(d) if d else None


class HerculaneumScan:
	def __init__(self, volpkg_path, vol_id, resolution_um, xray_energy_KeV, width, height, slices):
		self.volpkg_path = volpkg_path
		self.vol_id = vol_id
		self.resolution_um = resolution_um
		self.xray_energy_KeV = xray_energy_KeV
		self.width = width
		self.height = height
		self.slices = slices

	@property
	def volpkg_dir(self):
		return get_data_dir() / self.volpkg_path.replace('/', os.sep)

	def filepath(self, path):
		return self.volpkg_dir / path.replace('/', os.sep)

	def url(self, path):
		return f"{DATA_URL}/{self.volpkg_path}/{path}"

	@property
	def small_volume_path(self):
		return f"volumes_small/{self.vol_id}_small.tif"

	@property
	def small_volume_filepath(self):
		return self.filepath(self.small_volume_path)

	@property
	def small_volume_url(self):
		return self.url(self.small_volume_path)

	def grid_cell_name(self, jx, jy, jz):
		return f"cell_yxz_{jy+1:03}_{jx+1:03}_{jz+1:03}"

	def grid_cell_filename(self, jx, jy, jz):
		return f"{self.grid_cell_name(jx, jy, jz)}.tif"

	def grid_cell_path(self, jx, jy, jz):
		return f"volume_grids/{self.vol_id}/{self.grid_cell_filename(jx, jy, jz)}"

	def grid_cell_filepath(self, jx, jy, jz):
		return self.filepath(self.grid_cell_path(jx, jy, jz))

	def grid_cell_url(self, jx, jy, jz):
		return self.url(self.grid_cell_path(jx, jy, jz))

	def grid_cell_holes_dir(self, jx, jy, jz):
		return self.filepath(f"segmentation/{self.grid_cell_name(jx,jy,jz)}/holes")

	def grid_cell_patches_dir(self, jx, jy, jz):
		return self.filepath(f"segmentation/{self.grid_cell_name(jx,jy,jz)}/patches")

	def segments_dir(self):
		return self.filepath("paths")

SCANS = {
	"scroll_1a_791_54" : HerculaneumScan("full-scrolls/Scroll1/PHercParis4.volpkg", "20230205180739", 7.91, 54.0,  8096,  7888, 14376),
	"scroll_1b_791_54" : HerculaneumScan("full-scrolls/Scroll1/PHercParis4.volpkg", "20230206171837", 7.91, 54.0,  8316,  7812, 10532),
	"scroll_2a_791_54" : HerculaneumScan("full-scrolls/Scroll2/PHercParis3.volpkg", "20230210143520", 7.91, 54.0, 11984, 10112, 14428),
	"scroll_2a_791_88" : HerculaneumScan("full-scrolls/Scroll2/PHercParis3.volpkg", "20230212125146", 7.91, 88.0, 11136,  8480,  1610),
	"scroll_2b_791_54" : HerculaneumScan("full-scrolls/Scroll2/PHercParis3.volpkg", "20230206082907", 7.91, 54.0, 11296,  8448,  6586),
	"scroll_3_324_53"  : HerculaneumScan("full-scrolls/Scroll3/PHerc332.volpkg",    "20231027191953", 3.24, 53.0,  9414,  9414, 22941),
	"scroll_3_791_53"  : HerculaneumScan("full-scrolls/Scroll3/PHerc332.volpkg",    "20231117143551", 7.91, 53.0,  3400,  3550,  9778),
	"scroll_3_324_70"  : HerculaneumScan("full-scrolls/Scroll3/PHerc332.volpkg",    "20231201141544", 3.24, 70.0,  9414,  9414, 22932),
	"scroll_4_324_88"  : HerculaneumScan("full-scrolls/Scroll4/PHerc1667.volpkg",   "20231107190228", 3.24, 88.0,  8120,  7960, 26391),
	"scroll_4_791_53"  : HerculaneumScan("full-scrolls/Scroll4/PHerc1667.volpkg",   "20231117161658", 7.91, 53.0,  3440,  3340, 11174),
	"fragment_1_324_54": HerculaneumScan("fragments/Frag1/PHercParis2Fr47.volpkg",  "20230205142449", 3.24, 54.0,  7198,  1399,  7219),
	"fragment_1_324_88": HerculaneumScan("fragments/Frag1/PHercParis2Fr47.volpkg",  "20230213100222", 3.24, 88.0,  7332,  1608,  7229),
	"fragment_2_324_54": HerculaneumScan("fragments/Frag2/PHercParis2Fr143.volpkg", "20230216174557", 3.24, 54.0,  9984,  2288, 14111),
	"fragment_2_324_88": HerculaneumScan("fragments/Frag2/PHercParis2Fr143.volpkg", "20230226143835", 3.24, 88.0, 10035,  2112, 14144),
	"fragment_3_324_88": HerculaneumScan("fragments/Frag3/PHercParis1Fr34.volpkg",  "20230212182547", 3.24, 88.0,  6108,  1644,  6650),
	"fragment_3_324_54": HerculaneumScan("fragments/Frag3/PHercParis1Fr34.volpkg",  "20230215142309", 3.24, 54.0,  6312,  1440,  6656),
	"fragment_4_324_54": HerculaneumScan("fragments/Frag4/PHercParis1Fr39.volpkg",  "20230215185642", 3.24, 54.0,  5808,  1968,  9231),
	"fragment_4_324_88": HerculaneumScan("fragments/Frag4/PHercParis1Fr39.volpkg",  "20230222173037", 3.24, 88.0,  5957,  1969,  9209),
	"fragment_5_324_70": HerculaneumScan("fragments/Frag5/PHerc1667Cr1Fr3.volpkg",  "20231121133215", 3.24, 70.0,  4420,  1400,  7010),
	"fragment_5_791_70": HerculaneumScan("fragments/Frag5/PHerc1667Cr1Fr3.volpkg",  "20231130111236", 7.91, 70.0,  2046,   668,  3131),
	"fragment_6_324_53": HerculaneumScan("fragments/Frag6/PHerc51Cr4Fr8.volpkg",    "20231121152933", 3.24, 53.0,  6300,  2260,  8855),
	"fragment_6_791_53": HerculaneumScan("fragments/Frag6/PHerc51Cr4Fr8.volpkg",    "20231130112027", 7.91, 53.0,  2724,  1068,  3683),
	"fragment_6_324_88": HerculaneumScan("fragments/Frag6/PHerc51Cr4Fr8.volpkg",    "20231201112849", 3.24, 88.0,  6300,  2260,  8855),
	"fragment_6_324_70": HerculaneumScan("fragments/Frag6/PHerc51Cr4Fr8.volpkg",    "20231201120546", 3.24, 70.0,  6300,  2260,  8855),
}


# World to grid coordinates (jx, jy, jz), 0-indexed.
def world_to_grid(v):
	return (int(v.x // 5), int(v.y // 5), int(v.z // 5))


def download_file(scan, path):
	filepath = scan.filepath(path)
	if filepath.is_file():
		return
	url = scan.url(path)
	if not filepath.parent.is_dir():
		os.makedirs(filepath.parent)
	response = requests.get(url, auth=HTTPBasicAuth('registeredusers', 'only'), stream=True)
	if not response.ok:
		return
	# size = int(response.headers.get("Content-Length", 1e9))
	# size_downloaded = 0
	with open(filepath, "wb") as file:
		for data in response.iter_content(chunk_size=None):
			file.write(data)
			# size_downloaded += len(data)
			# context.window_manager.progress_update(min(size_downloaded/size, 1)
	print(f"Finished downloading {path}")


# Fire and forget. A progress bar somewhere would be best. At least show status:
# Use a ThreadPoolExecutor and check status from the main thread by registering
# a function f with bpy.app.timers.register(f), and have f check status by
# calling concurrent.futures.wait(dlfuts, timeout=0, return_when=FIRST_COMPLETED).
# Also, a way to dedupe concurrent calls is needed. Checking that the file
# exists is not enough.
def download_file_start(scan, path, context):
	filepath = scan.filepath(path)
	if filepath.is_file():
		return
	print(f"Downloading {path}...")
	thread = threading.Thread(target=download_file, args=(scan, path))
	thread.start()
