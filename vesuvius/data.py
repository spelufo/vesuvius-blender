import os

# Source data ##################################################################

DATA_URL = "http://dl.ash2txt.org"

class HerculaneumScan:
	def __init__(self, volpkg_path, vol_id, resolution_um, xray_energy_KeV, width, height, slices):
		self.volpkg_path = volpkg_path
		self.vol_id = vol_id
		self.resolution_um = resolution_um
		self.xray_energy_KeV = xray_energy_KeV
		self.width = width
		self.height = height
		self.slices = slices

SCANS = {
	"scroll_1_54": HerculaneumScan(
		"full-scrolls/Scroll1.volpkg", "20230205180739", 7.91, 54,  8096,  7888, 14376),
	"scroll_2_54": HerculaneumScan(
		"full-scrolls/Scroll2.volpkg", "20230210143520", 7.91, 54, 11984, 10112, 14428),
	"scroll_2_88": HerculaneumScan(
		"full-scrolls/Scroll2.volpkg", "20230212125146", 7.91, 88, 11136,  8480,  1610),
	"fragment_1_54": HerculaneumScan(
		"fragments/Frag1.volpkg",      "20230205142449", 3.24, 54,  7198,  1399,  7219),
	"fragment_1_88": HerculaneumScan(
		"fragments/Frag1.volpkg",      "20230213100222", 3.24, 88,  7332,  1608,  7229),
	"fragment_2_54": HerculaneumScan(
		"fragments/Frag2.volpkg",      "20230216174557", 3.24, 54,  9984,  2288, 14111),
	"fragment_2_88": HerculaneumScan(
		"fragments/Frag2.volpkg",      "20230226143835", 3.24, 88, 10035,  2112, 14144),
	"fragment_3_54": HerculaneumScan(
		"fragments/Frag3.volpkg",      "20230215142309", 3.24, 54,  6312,  1440,  6656),
	"fragment_3_88": HerculaneumScan(
		"fragments/Frag3.volpkg",      "20230212182547", 3.24, 88,  6108,  1644,  6650),
}


# def zpad(i, ndigits):
# 	return str(i).zfill(ndigits)

# def scan_slice_filename(scan, iz):
# 	ndigits = int(np.ceil(np.log10(scan.slices)))
# 	return zpad(iz - 1, ndigits) + ".tif"

# def scan_slice_server_path(scan, iz):
# 	return f"{scan.path}/{scan_slice_filename(scan, iz)}"

# def scan_slice_path(scan, iz):
# 	return os.path.join(DATA_DIR, scan_slice_server_path(scan, iz))

# def scan_slice_url(scan, iz):
# 	return f"{DATA_URL}/{scan_slice_server_path(scan, iz)}"

# def scan_dimensions_mm(scan):
# 	return scan.resolution_um * np.array([scan.width, scan.height, scan.slices]) / 1000

# def scan_position_mm(scan, iy, ix, iz):
# 	return scan.resolution_um * np.array([ix - 1, iy - 1, iz - 1]) / 1000


# Grid #########################################################################

# GRID_DIR = DATA_DIR
# GRID_SIZE = 500  # The size of each cell.

# def grid_size(scan, dim=None):
# 	size = (int(np.ceil(scan.height / GRID_SIZE)),
# 			int(np.ceil(scan.width / GRID_SIZE)),
# 			int(np.ceil(scan.slices / GRID_SIZE)))

# 	return size if dim is None else size[dim]

# def grid_cell_range(j, max_val):
# 	return slice(GRID_SIZE * (j - 1), min(GRID_SIZE * j, max_val))

# def grid_cell_filename(scan, jy, jx, jz):
# 	return f"cell_yxz_{zpad(jy, 3)}_{zpad(jx, 3)}_{zpad(jz, 3)}.tif"

# def grid_cell_server_path(scan, jy, jx, jz):
# 	path = scan.path.replace("/volumes/", "/volume_grids/")
# 	return f"{path}/{grid_cell_filename(scan, jy, jx, jz)}"

# def grid_cell_path(scan, jy, jx, jz):
# 	return os.path.join(GRID_DIR, grid_cell_server_path(scan, jy, jx, jz))

# def have_grid_cell(scan, jy, jx, jz):
# 	return os.path.isfile(grid_cell_path(scan, jy, jx, jz))

# def have_grid_cells(scan, jys, jxs, jz):
# 	for jy in jys:
# 		for jx in jxs:
# 			if not have_grid_cell(scan, jy, jx, jz):
# 				return False
# 	return True

# def load_grid_cell(scan, jy, jx, jz):
# 	return io.imread(grid_cell_path(scan, jy, jx, jz))


# Small ########################################################################

# SMALL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_small")
# SMALLER_BY = 10

# def small_size(scan):
# 	return (len(range(0, scan.height, SMALLER_BY)),
# 			len(range(0, scan.width, SMALLER_BY)),
# 			len(range(0, scan.slices, SMALLER_BY)))

# def small_slice_path(scan, iz):
# 	return os.path.join(SMALL_DIR, scan.path, scan_slice_filename(scan, iz))

# def small_volume_path(scan):
# 	return os.path.join(SMALL_DIR, f"{scan.path}_small.tif")

# def load_small_volume(scan, mmap=True):
# 	return io.imread(small_volume_path(scan), plugin='tifffile', as_gray=False)
