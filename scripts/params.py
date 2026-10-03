"""All design parameters for the articulated dog (mm, degrees).

Coordinate system (assembled dog): +x = nose direction, +z = up, +y = dog's left.
The reference drawing is the view from -y (dog facing right).
Drawing pixel -> model mm:  x = (px-125)*PX,  z = (1060-py)*PX
"""
PX = 0.1514            # mm per source-image pixel (sets overall size: 925 px drawing length -> 140 mm)
VOXEL = 0.4            # SDF sampling pitch for the organic shells
SIMPLIFY_TOL = 0.02    # mesh simplification tolerance

# ---------------- body ----------------
BODY_HALF_W = 16.0     # torso / thigh half width (y)
BODY_EDGE_R = 8.0      # lateral rounding of torso
BACK_Z = 74.0          # top of back
TORSO_PROFILE = [(1.5, 32), (1.5, BACK_Z), (103, BACK_Z), (103, 33), (84, 33), (84, 62.5),
                 (46, 62.5), (46, 53), (34, 30)]
BELLY_BOX = dict(x0=56, x1=80, z0=41, z1=63, half_w=12.0, edge_r=3.0)
CHEST_PROFILE = [(96, 58), (107, 54.5), (120.5, 54.5), (120.5, 51.0), (102, 33.0), (96, 33.5)]
CHEST_HALF_W = 8.5
CHEST_EDGE_R = 4.0
LEG_HALF_W = 5.5       # leg half thickness in y  (11 mm thick legs)
LEG_EDGE_R = 2.6
LEG_Y = 10.5           # leg centre offset in y
# legs: (x_back, x_front, toe_len, side) ; side -1 = near (reference) side, +1 = far side
LEGS = [(4.0, 18.0, 3.5, -1), (18.0, 31.5, 3.5, +1),      # hind near / far
        (84.0, 95.5, 3.0, -1), (90.5, 102.0, 3.0, +1)]    # front near / far
LEG_TOP_Z = 40.0
BODY_BLUR = 1.4        # gaussian rounding (mm)

# ---------------- head ----------------
HEAD_BOTTOM_Z = 55.0
CRANIUM = dict(c=(117.0, 0, 67.0), half=(15.0, 13.0, 17.0), r=10.0)
MUZZLE = dict(c=(133.0, 0, 61.0), half=(7.2, 7.5, 9.0), r=4.0)
NOSE = dict(c=(139.4, 0, 66.3), r=2.6)
# ears: base point, tip point, base radius, tip radius (near ear set back, far ear forward, as drawn)
EARS = [((118.0, -7.0, 80.0), (119.5, -8.5, 94.5), 5.2, 1.5),
        ((123.0, 7.0, 80.0), (124.8, 8.5, 92.5), 5.2, 1.5)]
EYE = dict(x=125.5, z=70.3, y=12.9, r=2.3)
MOUTH = dict(z=59.6, half_h=0.5, depth=0.8, x_min=131.0)
HEAD_BLUR = 0.6

# ---------------- tail ----------------
TAIL_HALF_W = 4.9      # half thickness in y (flat faces -> prints lying on its side)
TAIL_EDGE_R = 2.4
# centre-line (x, z, in-plane radius)
TAIL_PATH = [(11.5, 73.75, 6.5), (11.3, 78, 5.6), (8.5, 85, 4.8), (5.2, 92, 4.5), (5.0, 98, 4.4),
             (8.0, 103.5, 4.3), (14.0, 106.3, 4.2), (20.0, 105.8, 4.2), (23.5, 103.2, 4.4)]
TAIL_BLUR = 0.5

# ================= JOINT A : head ball joint =================
BALL_C = (114.0, 0.0, 66.0)   # ball centre
BALL_R = 6.0                  # ball radius (male, on body)
SOCKET_CLEAR = 0.10           # radial clearance socket-ball (female radius = BALL_R + this)
BALL_FLAT = 3.8               # ball is trimmed to |x-xc| <= this so the two halves can pass the throat
THROAT_BELOW = 1.6            # socket throat (min opening) is this far below ball centre
TUNNEL_R_BOTTOM = 7.6         # entry radius of tunnel at head bottom
STALK_R = 3.7
STALK_FILLET_R = 4.3          # base radius of the small conical fillet at the bottom of the moat
MOAT_R = 4.9                  # relief moat around the stalk (lengthens the flexing halves)
MOAT_BOTTOM_Z = 51.0
BALL_SPREAD = 0.25            # each ball half is modelled this far outward (y): preload = spread - SOCKET_CLEAR
SLOT_W = 2.0                  # slot through ball+stalk (halves flex in y)
SLOT_BOTTOM_Z = 51.0
HEAD_CARVE_CLEAR = 0.8        # clearance between swept head and body
HEAD_YAW = 90.0               # design yaw range +/-
HEAD_PITCH = 15.0             # design nod range +/-
HEAD_ROLL = 12.0              # design sideways tilt +/-

# ================= JOINT B : tail swivel snap pin =================
TAIL_AXIS = (11.5, 0.0)       # vertical axis x,y
SEAT_Z = 73.6                 # spot-face on body
TAIL_ROOT_Z = 73.75           # tail root face (0.15 nominal gap; tail rests on seat)
SEAT_R = 8.5
PEG_R = 5.0                   # peg shank radius (male)
BORE_CLEAR = 0.20             # radial clearance of bore (female radius = PEG_R + this)
PEG_LEN = 21.5
PEG_SLOT_W = 3.6              # slot between the two snap arms (arms flex in x of the tail plane)
BARB_H = 0.5                  # barb radial engagement beyond bore radius
BARB_TOP = 16.6               # depth below tail root where barb return face starts
BARB_AX_CLEAR = 0.3           # axial clearance barb / ledge
BARB_HALF_Y = 3.0             # barb exists only for |y| <= this (so arms can pass the bore)
BAND_INTERF = 0.10            # friction band radial interference with bore
CAVITY_CLEAR = 0.4            # radial clearance of barb in undercut cavity
BORE_DEPTH = 22.6
HEAD_TILT_TOTAL = 15.7       # combined tilt (hypot of pitch and roll) the stalk/tunnel allows with margin
