SHADER_TEMPLATE = """
struct Scan {
	string small_path;
	string grid_pathfmt;
	float res;
	vector dims;
	vector minj;
	vector maxj;
};

float texture3d_fixed_up(string path, point ptex, float zres) {
	int zindex = int(zres-1)*ptex.z;
	float zcorrection = 2*(ptex.z - 0.5)*(ptex.z - 0.5) + 0.5;
	return zcorrection*texture3d(path, ptex, "subimage", zindex);
}

float sample_scan(Scan scan, point p) {
	float celldim = 5;
	p -= 0.02; // Not sure exactly why this is needed, but it is.
	vector j = p / celldim;
	if (j.x > scan.minj.x && j.x <= scan.maxj.x &&
	    j.y > scan.minj.y && j.y <= scan.maxj.y &&
	    j.z > scan.minj.z && j.z <= scan.maxj.z) {
		// grid cell
		int jx = ceil(j.x); int jy = ceil(j.y); int jz = ceil(j.z);
		point ptex = p / celldim - vector(jx-1, jy-1, jz-1);
		return texture3d_fixed_up(format(scan.grid_pathfmt, jy, jx, jz), ptex, 500);
	} else {
		// small
		point ptex = p / scan.dims;
		return texture3d_fixed_up(scan.small_path, ptex, 10*scan.dims.z);
	}
}

float measure_scan(Scan scan, point p) {
	float v = sample_scan(scan, p);
	return max(0, (v - 0.15)/1.15);
}

shader vesuvius_scan(
	float offset_um = 0,
	float nmerge_samples = 3,
	float nmerge_step_um = 7.91,
	int disable_hires = 0,
	vector MinJ = vector(0, 0, 0),
	vector MaxJ = vector(0, 0, 0),
	output color Value = color(1, 0, 1),
	) {
	vector min_j = vector(1,0,0);
	vector max_j = vector(0,0,0);
	if (!disable_hires) {
		min_j = MinJ;
		max_j = MaxJ;
	}

	Scan scan = SCAN_LITERAL;
	float offset = offset_um / scan.res;
	float nmerge_step = nmerge_step_um / scan.res;
	if (backfacing()>0) offset = -offset;


	float value = 0;
	value += measure_scan(scan, P - (offset)*N);
	Value.r = value;
	value += measure_scan(scan, P - (offset + nmerge_step)*N);
	Value.g = value/2;
	value += measure_scan(scan, P - (offset + 2*nmerge_step)*N);
	Value.b = value/3;

	/*
	float value = 0;
	for (int i = 0; i < nmerge_samples; i++) {
		value += measure_scan(scan, P - (offset + i*nmerge_step)*N);
	}
	Value = value/nmerge_samples;
	*/
}
"""


def osl_str(s):
	return '"' + repr(str(s))[1:-1] + '"'

def generate_shader(scan):
	print("generate_shader")
	small_path = scan.small_volume_filepath
	grid_pathfmt = scan.volpkg_dir / "volume_grids" / scan.vol_id / "cell_yxz_%03d_%03d_%03d.tif"
	res = scan.resolution_um * 100
	dimsx, dimsy, dimsz = scan.width / 100, scan.height / 100, scan.slices / 100
	dims = f"vector({dimsx}, {dimsy}, {dimsz})"
	scan = f"Scan({osl_str(small_path)}, {osl_str(grid_pathfmt)}, {res}, {dims}, min_j, max_j)"
	return SHADER_TEMPLATE.replace("SCAN_LITERAL", scan)

