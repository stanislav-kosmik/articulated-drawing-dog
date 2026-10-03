"""Design parameters for the articulated drawing-dog, version 2 (mm, degrees).

Frame: +x = nose, +z = up, +y = dog's left.  The drawing is the view from -y ("near" side).
All silhouette landmarks are given in SOURCE-IMAGE PIXELS and converted with px()/P().
"""
S = 0.158      # mm per image pixel (954 px drawing length -> ~150 mm)
X0 = 103.0     # image x of the rearmost point (tail outer curve)
Y0 = 1048.0    # image y of the ground line
VOXEL = 0.4
SIMPLIFY_TOL = 0.02
BLUR = 0.9     # global soft rounding (mm)

def P(pts):
    return [((x - X0) * S, (Y0 - y) * S) for x, y in pts]
def fx(x): return (x - X0) * S
def fz(y): return (Y0 - y) * S

# ------------------------------------------------------------------ silhouette (image pixels)
BELLY_PY = 722        # belly line of the rear/front torso stubs = underside of the joint tongues
MID_BELLY_PY = 790    # bottom edge of the middle piece (the box in the drawing)
MID_BOX_TOP_PY = 640
TORSO_PX = [(118, 604), (215, 548), (445, 560), (650, 572), (748, 582),      # rump top -> back line -> neck base
            (806, 790), (798, 802), (720, 802),                              # inside chest -> chest bottom
            (640, 722), (503, 722),                                          # 45deg gusset to belly, belly line
            (420, 805), (380, 830), (104, 830), (104, 800), (108, 700)]      # thigh diagonal, haunch bottom, rump
NECK_HEAD_PX = [(700, 585), (748, 582), (790, 572), (850, 523), (885, 503), (900, 497), (960, 505), (985, 555),
                (1000, 595), (1000, 690), (950, 691), (900, 700), (860, 720), (830, 750), (806, 790), (798, 802),
                (760, 802), (700, 700)]
MUZZLE_PX = [(950, 600), (1000, 595), (1035, 603), (1050, 625), (1056, 655), (1050, 688), (1000, 690), (950, 691)]
TAIL_PX = [(118, 620), (118, 612), (106, 560), (103, 500), (108, 450), (122, 410), (150, 370), (185, 345), (225, 331),
           (262, 330), (288, 340), (298, 353), (294, 358),                   # outer curve -> tip
           (181, 437), (172, 470), (176, 505), (192, 530), (215, 548), (215, 620)]  # inner curve (chord >= 35deg so it prints unsupported)
# legs: polygon (px), side (-1 near / +1 far)
LEGS_PX = [
    ([(104, 1070), (104, 800), (424, 800), (228, 996), (228, 1012), (254, 1024), (257, 1070)], -1),   # rear leg 1 (near) + 45deg thigh
    ([(257, 1070), (257, 800), (410, 800), (380, 830), (342, 890), (327, 950), (330, 1000), (352, 1030), (352, 1070)], +1),  # rear leg 2 (far)
    ([(650, 1070), (650, 722), (714, 722), (714, 1010), (724, 1022), (726, 1070)], +1),               # front leg A (far)
    ([(730, 1070), (730, 800), (798, 800), (796, 830), (796, 1010), (806, 1022), (808, 1070)], -1),   # front leg B (near)
]
EARS_PX = [((905, 512), (915, 437), -6.5), ((950, 515), (952, 453), +6.5)]   # base, tip, y
EAR_R = (4.4, 1.7)
EYE_PX = (935, 598)
EYE_R = 2.0

# ------------------------------------------------------------------ lateral thickness
BODY_HALF_W = 15.0;  BODY_EDGE_R = 8.0
HEAD_HALF_W = 11.5;  HEAD_EDGE_R = 6.0
MUZZLE_HALF_W = 8.0; MUZZLE_EDGE_R = 4.5
TAIL_HALF_W = 5.0;   TAIL_EDGE_R = 4.2
LEG_HALF_W = 5.75;   LEG_EDGE_R = 3.0;  LEG_Y = 9.25
MID_CHAMFER = 4.0     # 45deg chamfer on the bottom edges of the middle piece (prints belly-down)

# ------------------------------------------------------------------ the two joints (vertical-axis snap pivots)
SEAM_A_PX = 485       # where seam A meets the side wall (image x)
SEAM_B_PX = 650
SEAM_R = 18.0         # radius of the cylindrical seam about each pivot axis
SEAM_GAP = 0.5        # gap between the concentric seam faces
POST_R = 5.5          # pivot post (part of rear / front)
CLIP_T = 1.8          # radial thickness of the C-clip arms (part of middle)
CLIP_PRELOAD = 0.10   # clip bore is this much smaller (radius) than the post -> elastic grip = friction
MOUTH_HALF_ANGLE = 72.0   # half opening angle of the C-clip mouth
NECK_W = 6.0          # width of the tongue neck
TONGUE_T = 7.0        # tongue thickness (vertical)
FLOOR_CLEAR = 0.30    # clearance under the tongue
CEIL_CLEAR = 0.35     # clearance above the tongue (ceiling is a short printed bridge around the post)
POCKET_RADIAL = 0.9   # radial room around the clip ring (lets the arms open while snapping)
CORRIDOR_EXTRA = 0.7  # the straight insertion corridor is this much wider (per side) than the clip ring
SIDE_CLEAR = 0.40     # clearance between neck and the stop faces of the sector
YAW_RANGE = 30.0      # usable yaw each side
YAW_STOP_MARGIN = 1.0 # the sector is cut this much wider than YAW_RANGE
NOSE_CHAMFER_D = 8.3  # beyond this distance from the pivot the pocket ceiling rises at 45deg (self-supporting, no bridge)
