"""Football Scheme Playbook & Chalkboard Formation Specs for ddyno Why Watch.

Every offensive and defensive scheme classified by watch.py has a matching entry here with:
  - side: 'offense' or 'defense'
  - tagline: short 1-line summary
  - entails: what the scheme actually does and how it stresses the opponent
  - example: a concrete snap-by-snap on-field example showing what happens when it's called
  - works_when / counter: strengths and how opponents beat it
  - formation: base personnel / alignment name shown under the diagram
  - diagram: declarative chalkboard data (LOS at y=122 in a 360x210 field)
      off:   [[x, y, label, kind], ...]   kind in ('ol','qb','rb','te','wr')
      def:   [[x, y, label], ...]
      routes: [{"pts": [[x,y],...], "kind": "primary"|"route"|"fake"|"block"|"blitz"|"drop"}, ...]
      zones:  [{"cx": x, "cy": y, "rx": rx, "ry": ry, "lbl": "..."}, ...]
"""
from __future__ import annotations

# Standard 5-man offensive line centered at x=180, LOS y=122
OL = [
    [144, 130, "LT", "ol"],
    [162, 130, "LG", "ol"],
    [180, 128, "C",  "ol"],
    [198, 130, "RG", "ol"],
    [216, 130, "RT", "ol"],
]

# Light reference defense (4-3 / Nickel shell) for offensive diagrams so the viewer sees the clash
REF_DEF_TWO_HIGH = [
    [146, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [214, 114, "DE"],
    [156, 94, "LB"], [204, 94, "LB"],
    [46, 100, "CB"], [314, 100, "CB"], [266, 96, "NB"],
    [128, 52, "S"], [232, 52, "S"],
]

REF_DEF_SINGLE_HIGH = [
    [144, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [218, 114, "DE"],
    [146, 94, "LB"], [180, 92, "LB"], [214, 94, "LB"],
    [46, 102, "CB"], [314, 102, "CB"], [246, 86, "SS"],
    [180, 46, "FS"],
]

# Light reference offense (11 personnel) for defensive diagrams
REF_OFF_11 = OL + [
    [180, 152, "QB", "qb"],
    [162, 166, "RB", "rb"],
    [234, 132, "TE", "te"],
    [44,  130, "WR", "wr"],
    [276, 138, "WR", "wr"],
    [318, 130, "WR", "wr"],
]

SCHEMES: dict[str, dict] = {
    # ============================================================== OFFENSIVE SCHEMES
    "Air Raid / Spread Offense": {
        "side": "offense",
        "tagline": "Four-wide spacing that stretches defenses horizontally and vertically every snap.",
        "entails": (
            "Lining up in shotgun with four receivers spread across the width of the field forces defenders out of the box "
            "and into open-space coverage. Instead of a massive playbook, the quarterback works quick progression reads—attacking "
            "deep seams if the safeties sit low, or taking instant underneath throws if corners bail."
        ),
        "example": (
            "On 2nd-and-8, the offense aligns in 10 personnel (four wide, one back) and calls Four Verticals. "
            "Both slot receivers sprint up the seams while the outside receivers push the corners deep; the single high safety "
            "can only lean toward one seam, so the quarterback looks him left and rifles a 22-yard strike up the right hash before the linebacker can get depth."
        ),
        "works_when": "Pass protection holds for 2.5+ seconds and receivers win 1-on-1 leverage in space.",
        "counter": "Drop 7–8 into two-high zones, disguise post-snap rotations, and get pressure with a four-man rush.",
        "formation": "10 Personnel (2×2 Spread Shotgun) · Four Verticals / Seam Stretch",
        "diagram": {
            "off": OL + [
                [180, 156, "QB", "qb"], [202, 160, "RB", "rb"],
                [38, 130, "WR", "wr"], [96, 138, "WR", "wr"],
                [264, 138, "WR", "wr"], [322, 130, "WR", "wr"],
            ],
            "def": REF_DEF_SINGLE_HIGH,
            "routes": [
                {"pts": [[38, 126], [36, 36]], "kind": "route"},
                {"pts": [[96, 134], [122, 34]], "kind": "route"},
                {"pts": [[264, 134], [228, 34]], "kind": "primary"},
                {"pts": [[322, 126], [324, 36]], "kind": "route"},
                {"pts": [[202, 156], [218, 114], [190, 102]], "kind": "fake"},
            ],
            "zones": [],
        },
    },
    "Spread Passing Offense": {
        "side": "offense",
        "tagline": "High-volume shotgun passing using trips spacing and high-low zone conflicts.",
        "entails": (
            "Lives out of 11 personnel (3 WR, 1 TE, 1 RB) in shotgun with high pass rates on early downs. "
            "The goal is to overload one side of a zone defense—putting three receivers into a two-defender area "
            "so one route is guaranteed to break open at the intermediate or underneath level."
        ),
        "example": (
            "On 3rd-and-5, the offense sets three receivers to the right (Trips) and runs a Flood concept: the outside receiver clears out "
            "the corner on a deep fade, the middle slot bends to the sideline at 12 yards, and the tight end releases into the flat at 4 yards. "
            "When the flat defender widens toward the tight end, the quarterback hits the 12-yard out cleanly along the sideline for a first down."
        ),
        "works_when": "The quarterback reads zone leverage cleanly and converts 3rd downs without forcing throws.",
        "counter": "Rally-and-tackle underneath, mix quarters/match coverage to pass off trips routes, and stiffen in the red zone.",
        "formation": "11 Personnel (3×1 Trips Shotgun) · High-Low Sideline Flood",
        "diagram": {
            "off": OL + [
                [180, 156, "QB", "qb"], [156, 160, "RB", "rb"],
                [42, 130, "WR", "wr"],
                [234, 132, "TE", "te"], [278, 138, "WR", "wr"], [322, 130, "WR", "wr"],
            ],
            "def": REF_DEF_TWO_HIGH,
            "routes": [
                {"pts": [[322, 126], [332, 36]], "kind": "route"},
                {"pts": [[278, 134], [278, 72], [330, 68]], "kind": "primary"},
                {"pts": [[234, 128], [248, 104], [298, 98]], "kind": "route"},
                {"pts": [[42, 126], [42, 82], [96, 82]], "kind": "route"},
            ],
            "zones": [],
        },
    },
    "West Coast Play-Action": {
        "side": "offense",
        "tagline": "Under-center outside zone paired with illusion-heavy play-action chunk throws.",
        "entails": (
            "Makes every run and pass look identical for the first two seconds after the snap. "
            "Using pre-snap motion and condensed splits (21 or 12 personnel), the offense forces linebackers to sprint laterally "
            "against outside zone—then pulls the ball on play-action to rip deep crossers and bootlegs into the wide-open space behind them."
        ),
        "example": (
            "On 1st-and-10, a receiver motions across the formation as the offensive line fires right to sell an outside-zone run. "
            "Both linebackers bite hard toward the right sideline; the quarterback fakes the handoff, boots left, and finds a receiver "
            "gliding across the empty middle of the field at 18 yards for an easy 28-yard chunk gain."
        ),
        "works_when": "Early-down runs stay on schedule so linebackers have to respect the fake, opening huge voids behind them.",
        "counter": "Win the line of scrimmage with disciplined edge setting so linebackers don't over-pursue, and disrupt bootlegs with a backside contain rusher.",
        "formation": "21 Personnel (Under Center / Motion) · Outside-Zone Play-Action Boot",
        "diagram": {
            "off": OL + [
                [180, 144, "QB", "qb"], [180, 168, "RB", "rb"], [200, 154, "FB", "rb"],
                [234, 132, "TE", "te"], [64, 132, "WR", "wr"], [286, 138, "WR", "wr"],
            ],
            "def": REF_DEF_SINGLE_HIGH,
            "routes": [
                {"pts": [[286, 138], [132, 142]], "kind": "fake"},
                {"pts": [[180, 164], [238, 148], [268, 118]], "kind": "fake"},
                {"pts": [[180, 144], [142, 162], [116, 148]], "kind": "fake"},
                {"pts": [[234, 128], [220, 96], [108, 66]], "kind": "primary"},
                {"pts": [[64, 128], [64, 42]], "kind": "route"},
                {"pts": [[200, 150], [164, 126], [88, 108]], "kind": "route"},
            ],
            "zones": [],
        },
    },
    "Power Run / Ground-and-Pound": {
        "side": "offense",
        "tagline": "Downhill gap-scheme rushing with extra blockers to wear down defensive fronts.",
        "entails": (
            "Uses heavy personnel (two tight ends or a fullback) to outnumber defenders at the point of attack. "
            "Linemen create double-teams on defensive tackles while a backside guard pulls around to kick out or lead through the hole, "
            "piling up 4–5 yard gains, chewing clock, and forcing defenses into 8-man boxes."
        ),
        "example": (
            "On 2nd-and-4, the offense lines up in 21 personnel I-Formation and calls Power-O right. "
            "The right tackle and tight end seal the defensive end inside, the fullback kicks out the outside linebacker, "
            "and the left guard pulls through the C-gap to wall off the middle linebacker—creating a clean alley for the running back to burst 11 yards downhill."
        ),
        "works_when": "The offensive line gets movement at the snap and stays ahead of the chains (4+ yards on 1st down).",
        "counter": "Shoot gaps for tackles for loss (TFLs), set a firm edge with a force defender, and force obvious 3rd-and-long passes.",
        "formation": "21 Personnel (I-Formation Heavy) · Power-O with Pulling Backside Guard",
        "diagram": {
            "off": OL + [
                [180, 144, "QB", "qb"], [180, 162, "FB", "rb"], [180, 180, "RB", "rb"],
                [234, 130, "TE", "te"], [50, 130, "WR", "wr"], [308, 132, "WR", "wr"],
            ],
            "def": REF_DEF_SINGLE_HIGH,
            "routes": [
                {"pts": [[162, 132], [186, 142], [220, 126], [222, 96]], "kind": "block"},
                {"pts": [[180, 158], [216, 142], [244, 110]], "kind": "block"},
                {"pts": [[180, 176], [202, 152], [224, 114], [230, 74]], "kind": "primary"},
                {"pts": [[198, 128], [192, 114]], "kind": "block"},
                {"pts": [[216, 128], [208, 112]], "kind": "block"},
                {"pts": [[234, 126], [228, 110]], "kind": "block"},
            ],
            "zones": [],
        },
    },
    "Run-Heavy Play-Action": {
        "side": "offense",
        "tagline": "Establishes the run from two-tight-end looks, then hits vertical shots off the fake.",
        "entails": (
            "Stays balanced toward the run with 12 personnel (two tight ends) so the defense has to keep extra defenders near the line of scrimmage. "
            "Once safeties start creeping into the box to stop inside zone, the offense dials up max-protect play-action shots down the seams and posts."
        ),
        "example": (
            "After three straight inside-zone runs move the chains, the offense comes back in the exact same 12-personnel set on 1st-and-10. "
            "The strong safety steps down toward the line on the run fake, leaving the deep middle single-covered—the quarterback plants off the fake "
            "and hits the receiver breaking behind the safety on a deep post for 34 yards."
        ),
        "works_when": "The run game forces 8-man boxes and leaves receivers 1-on-1 downfield.",
        "counter": "Stop the run with a light 6–7 man box so safeties can stay disciplined over the top.",
        "formation": "12 Personnel (Two Tight Ends) · Inside Zone Fake → Deep Post",
        "diagram": {
            "off": OL + [
                [180, 144, "QB", "qb"], [180, 170, "RB", "rb"],
                [126, 132, "TE", "te"], [234, 132, "TE", "te"],
                [44, 130, "WR", "wr"], [314, 130, "WR", "wr"],
            ],
            "def": REF_DEF_SINGLE_HIGH,
            "routes": [
                {"pts": [[180, 166], [196, 144], [202, 124]], "kind": "fake"},
                {"pts": [[314, 126], [306, 76], [216, 36]], "kind": "primary"},
                {"pts": [[44, 126], [48, 72], [134, 72]], "kind": "route"},
                {"pts": [[234, 128], [234, 114]], "kind": "block"},
                {"pts": [[126, 128], [116, 102], [78, 96]], "kind": "route"},
            ],
            "zones": [],
        },
    },
    "Run-and-Gun / Vertical Attack": {
        "side": "offense",
        "tagline": "Downfield air-yards attack hunting big plays, seams, and receiver choice routes.",
        "entails": (
            "Pushes the ball deep downfield (high average depth of target) instead of relying on short checkdowns. "
            "Receivers run option/choice stems—reading the defensive back's leverage on the fly to either burst vertically past press coverage "
            "or snap off deep comebacks and posts against soft cushion."
        ),
        "example": (
            "Out of a 3×1 spread alignment, the offense sends the outside receiver on a deep go/comeback choice while the slot attacks the vertical seam. "
            "Seeing the cornerback sit flat-footed at 6 yards with no safety help over top, the receiver bursts past him down the sideline "
            "and tracks a 38-yard bucket throw in stride."
        ),
        "works_when": "The offensive line buys time for deep routes to develop and receivers win 1-on-1 downfield matchups.",
        "counter": "Play disciplined two-high shell coverage to cap the deep ball and force checkdowns, while collapsing the pocket before routes break open.",
        "formation": "11 Personnel (Spread Verticals) · Deep Post-Wheel & Choice Stems",
        "diagram": {
            "off": OL + [
                [180, 156, "QB", "qb"], [158, 162, "RB", "rb"],
                [40, 130, "WR", "wr"], [234, 132, "TE", "te"],
                [276, 138, "WR", "wr"], [322, 130, "WR", "wr"],
            ],
            "def": REF_DEF_TWO_HIGH,
            "routes": [
                {"pts": [[40, 126], [40, 68], [120, 32]], "kind": "primary"},
                {"pts": [[322, 126], [322, 36]], "kind": "route"},
                {"pts": [[276, 134], [270, 74], [218, 42]], "kind": "route"},
                {"pts": [[158, 158], [108, 144], [84, 72]], "kind": "route"},
                {"pts": [[234, 128], [228, 114]], "kind": "block"},
            ],
            "zones": [],
        },
    },
    "West Coast Quick Game (YAC)": {
        "side": "offense",
        "tagline": "Fast-release timing throws and screens built to let playmakers create yards after the catch.",
        "entails": (
            "Gets the ball out of the quarterback's hands in under 2.4 seconds on slants, spacing concepts, and tunnel/bubble screens. "
            "Instead of asking linemen to pass-block for 4 seconds, it puts receivers in motion or tight bunches to create natural rubs and open-field 1-on-1s."
        ),
        "example": (
            "Facing a blitz look on 2nd-and-7, the offense lines up in a right-side Bunch set and runs a Slant-Flat / Rub concept. "
            "The point receiver releases inside to occupy the slot defender, clearing a clean runway for the trail receiver on a 5-yard slant; "
            "he catches it in full stride, splits two tacklers, and turns a 5-yard throw into a 21-yard gain."
        ),
        "works_when": "Receivers make the first defender miss in space and the quarterback beats the rush with instant timing.",
        "counter": "Jam receivers at the line to disrupt timing, rally multiple tacklers to the ball, and jump underneath throwing lanes.",
        "formation": "11 Personnel (Tight Bunch) · Quick Slant-Flat & Space Rub",
        "diagram": {
            "off": OL + [
                [180, 154, "QB", "qb"], [158, 160, "RB", "rb"],
                [46, 130, "WR", "wr"],
                [256, 130, "TE", "te"], [276, 140, "WR", "wr"], [296, 136, "WR", "wr"],
            ],
            "def": REF_DEF_TWO_HIGH,
            "routes": [
                {"pts": [[256, 126], [268, 92], [298, 72]], "kind": "route"},
                {"pts": [[276, 136], [264, 114], [202, 88]], "kind": "primary"},
                {"pts": [[296, 132], [326, 112], [340, 96]], "kind": "route"},
                {"pts": [[46, 126], [56, 106], [108, 94]], "kind": "route"},
            ],
            "zones": [],
        },
    },
    "Ball-Control Short Game": {
        "side": "offense",
        "tagline": "Low-risk, high-completion short passing designed to sustain long drives and avoid turnovers.",
        "entails": (
            "Prioritizes high-percentage completions (curls, sticks, checkdowns, and underneath crossers) over low-percentage deep shots. "
            "The offense takes whatever cushion the defense gives, steadily chaining 6–8 yard gains to stay out of negative plays and keep its defense rested."
        ),
        "example": (
            "On 2nd-and-6 against soft zone coverage, the offense calls a Stick concept to the right: the tight end sprints 6 yards and settles "
            "in the soft pocket outside the linebacker while the running back flares into the flat. "
            "The flat defender chases the back, so the quarterback hits the stationary tight end for an effortless 7-yard conversion."
        ),
        "works_when": "Drives stay penalty-free and turnover-free, converting 3rd-and-short consistently.",
        "counter": "Press receivers aggressively, squat on short hitches/sticks to jump routes, and force the offense to win vertically.",
        "formation": "11 Personnel (Balanced) · Stick / Curl-Flat Possession Read",
        "diagram": {
            "off": OL + [
                [180, 152, "QB", "qb"], [200, 160, "RB", "rb"],
                [46, 130, "WR", "wr"], [234, 132, "TE", "te"], [314, 130, "WR", "wr"], [104, 136, "WR", "wr"],
            ],
            "def": REF_DEF_TWO_HIGH,
            "routes": [
                {"pts": [[234, 128], [244, 96], [254, 102]], "kind": "primary"},
                {"pts": [[200, 156], [246, 136], [296, 112]], "kind": "route"},
                {"pts": [[314, 126], [314, 48]], "kind": "route"},
                {"pts": [[46, 126], [46, 80], [56, 88]], "kind": "route"},
                {"pts": [[104, 132], [116, 104], [156, 104]], "kind": "route"},
            ],
            "zones": [],
        },
    },
    "Pro-Style Offense": {
        "side": "offense",
        "tagline": "Balanced multiple-formation attack blending downhill runs with layered intermediate passing.",
        "entails": (
            "Mixes under-center and shotgun looks across 11 and 12 personnel without tipping run or pass by formation. "
            "Rather than leaning on one extreme, it adapts week-to-week to attack whatever weakness the opposing defense shows—running into light boxes and throwing layered intermediate routes against heavy fronts."
        ),
        "example": (
            "On 2nd-and-7 from a balanced 11-personnel set, the offense runs a Levels concept: a slot receiver crosses underneath at 5 yards "
            "while the outside receiver runs an intermediate dig right behind him at 14 yards. "
            "The middle linebacker steps up to cut off the shallow crosser, opening a clean window directly behind his ear for a 16-yard strike."
        ),
        "works_when": "Both run and pass stay efficient enough to keep the playbook wide open on every down.",
        "counter": "Win 1st down to push the offense into predictable passing situations where balanced play-calling disappears.",
        "formation": "11 Personnel (Multiple) · Layered Levels (Shallow + Intermediate Dig)",
        "diagram": {
            "off": OL + [
                [180, 148, "QB", "qb"], [180, 170, "RB", "rb"],
                [44, 130, "WR", "wr"], [234, 132, "TE", "te"],
                [280, 138, "WR", "wr"], [318, 130, "WR", "wr"],
            ],
            "def": REF_DEF_SINGLE_HIGH,
            "routes": [
                {"pts": [[318, 126], [318, 68], [186, 68]], "kind": "primary"},
                {"pts": [[280, 134], [268, 100], [166, 98]], "kind": "route"},
                {"pts": [[234, 128], [228, 76], [242, 46]], "kind": "route"},
                {"pts": [[44, 126], [44, 44]], "kind": "route"},
                {"pts": [[180, 166], [132, 144], [96, 114]], "kind": "route"},
            ],
            "zones": [],
        },
    },

    # ============================================================== DEFENSIVE SCHEMES
    "Blitz-Heavy / Pressure Defense": {
        "side": "defense",
        "tagline": "Crowds the line of scrimmage with disguised blitzes and simulated pressures to wreck QB timing.",
        "entails": (
            "Walks linebackers and defensive backs up to the line of scrimmage (often in Double-A-Gap mug looks) so the quarterback "
            "and offensive line cannot tell which 5 or 6 defenders are rushing and which are dropping into coverage. "
            "Forces rushed throws, sacks, and negative plays before deep routes ever develop."
        ),
        "example": (
            "On 3rd-and-6, the defense shows seven defenders across the line of scrimmage. At the snap, one A-gap linebacker drops out "
            "into the middle throwing lane while the slot corner fires unblocked off the edge; the protection slides away from the corner blitz, "
            "forcing an instant throwaway or a drive-killing sack."
        ),
        "works_when": "Disguise confuses pass protection and the rush hits home in under 2.5 seconds.",
        "counter": "Stay ahead of the chains on 1st down, hit quick hot-routes/screens behind the blitz, and punish single coverage if protection holds.",
        "formation": "Double-A-Gap Mug Front · Disguised Edge Blitz + Dropper",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [142, 114, "DE"], [170, 114, "LB"], [190, 114, "LB"], [218, 114, "DE"],
                [118, 112, "LB"], [266, 112, "NB"],
                [44, 102, "CB"], [318, 102, "CB"],
                [132, 56, "S"], [228, 56, "S"], [180, 76, "S"],
            ],
            "routes": [
                {"pts": [[266, 116], [244, 134], [192, 150]], "kind": "blitz"},
                {"pts": [[170, 118], [176, 144]], "kind": "blitz"},
                {"pts": [[142, 118], [156, 144]], "kind": "blitz"},
                {"pts": [[218, 118], [210, 144]], "kind": "blitz"},
                {"pts": [[118, 116], [142, 144]], "kind": "blitz"},
                {"pts": [[190, 110], [206, 86]], "kind": "drop"},
            ],
            "zones": [
                {"cx": 180, "cy": 46, "rx": 115, "ry": 22, "lbl": "Deep Help"},
            ],
        },
    },
    "Aggressive Man-Blitz (Boom-or-Bust)": {
        "side": "defense",
        "tagline": "Tight press-man coverage paired with penetrating fronts that trade big-play risk for havoc.",
        "entails": (
            "Asks cornerbacks to lock up receivers 1-on-1 in tight press-man with a single deep safety, freeing five or six defenders "
            "to shoot gaps for tackles for loss and sacks. It generates huge negative plays—but if the rush doesn't get home, receivers can hit home runs."
        ),
        "example": (
            "On 1st-and-10, both defensive tackles shoot downhill while an outside linebacker fires off the edge, blowing up an inside run "
            "for a 3-yard loss. On the next snap, they bring 5 again with press-man outside—if the quarterback survives the rush for 3 seconds, "
            "the lone deep safety is stretched thin and a double-move can break for 40 yards."
        ),
        "works_when": "Early-down TFLs and sacks keep the offense behind the chains before deep routes come open.",
        "counter": "Attack man coverage with crossing/rub routes, double-moves downfield, and quarterback scrambles into empty middle lanes.",
        "formation": "Cover 1 Press-Man · 5-Man Gap Penetration Blitz",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [140, 114, "DE"], [168, 114, "DT"], [194, 114, "DT"], [220, 114, "DE"],
                [146, 94, "LB"], [214, 94, "LB"],
                [44, 112, "CB"], [276, 112, "NB"], [318, 112, "CB"],
                [238, 96, "SS"], [180, 44, "FS"],
            ],
            "routes": [
                {"pts": [[140, 118], [154, 146]], "kind": "blitz"},
                {"pts": [[168, 118], [174, 142]], "kind": "blitz"},
                {"pts": [[194, 118], [188, 142]], "kind": "blitz"},
                {"pts": [[220, 118], [212, 146]], "kind": "blitz"},
                {"pts": [[146, 98], [158, 134], [172, 148]], "kind": "blitz"},
            ],
            "zones": [
                {"cx": 180, "cy": 42, "rx": 122, "ry": 24, "lbl": "Single-High FS"},
            ],
        },
    },
    "Ball-Hawk Zone / Cover 3": {
        "side": "defense",
        "tagline": "Three deep defenders and four underneath zones with eyes on the quarterback to hunt takeaways.",
        "entails": (
            "Divides the deep field into thirds (two outside corners + free safety) while four underneath defenders keep their eyes "
            "locked on the quarterback's shoulders instead of chasing receivers with their backs turned. That lets defenders break sharply on throws for PBUs and interceptions."
        ),
        "example": (
            "On 2nd-and-9, the strong safety buzzes down late into the hook/curl zone right after the snap. "
            "The quarterback expects the middle seam to be open against a single-high look, throws an intermediate dig, "
            "and the buzzing safety reads his eyes to step directly in front of the throw for an interception."
        ),
        "works_when": "Underneath defenders disguise their drops and turn aggressive intermediate throws into takeaways.",
        "counter": "Attack the deep seams between the safety and corners, or stretch the flat defenders horizontally with flood and curl-flat combinations.",
        "formation": "Cover 3 Buzz (3 Deep, 4 Underneath) · Late Safety Rotation",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [144, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [216, 114, "DE"],
                [152, 92, "LB"], [208, 92, "LB"],
                [46, 96, "CB"], [316, 96, "CB"], [268, 96, "NB"],
                [136, 54, "FS"], [228, 62, "SS"],
            ],
            "routes": [
                {"pts": [[136, 54], [180, 40]], "kind": "drop"},
                {"pts": [[228, 66], [216, 92]], "kind": "drop"},
                {"pts": [[46, 92], [54, 44]], "kind": "drop"},
                {"pts": [[316, 92], [308, 44]], "kind": "drop"},
            ],
            "zones": [
                {"cx": 64, "cy": 42, "rx": 52, "ry": 24, "lbl": "Deep 1/3"},
                {"cx": 180, "cy": 38, "rx": 56, "ry": 24, "lbl": "Deep 1/3"},
                {"cx": 296, "cy": 42, "rx": 52, "ry": 24, "lbl": "Deep 1/3"},
                {"cx": 146, "cy": 88, "rx": 38, "ry": 16, "lbl": "Hook"},
                {"cx": 224, "cy": 88, "rx": 38, "ry": 16, "lbl": "Buzz"},
            ],
        },
    },
    "Cover 2 / Two-High Shell": {
        "side": "defense",
        "tagline": "Two deep safeties cap every vertical route and dare the offense to march 12 plays without a mistake.",
        "entails": (
            "Keeps two safeties split deep (each protecting half the field) while corners squat in the flats and linebackers drop into intermediate windows. "
            "Its #1 rule is eliminating 20+ yard explosive passes—forcing offenses to execute long, patient drives where one penalty or sack ends the possession."
        ),
        "example": (
            "Facing an explosive passing offense on 1st-and-10, both safeties immediately gain depth to 16+ yards at the snap, "
            "bracketing the deep crossers and outside go routes. With nothing open downfield, the quarterback checks down to the running back "
            "for 4 yards and gets tackled immediately by the flat corner."
        ),
        "works_when": "The defense tackles cleanly underneath and forces impatient quarterbacks to test double-covered deep windows.",
        "counter": "Run the ball patiently into the lighter box, attack the deep middle hole between the two safeties, or work high-low sideline throws.",
        "formation": "Cover 2 / Tampa 2 Shell · Two Deep Halves + Middle-Hole Runner",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [144, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [216, 114, "DE"],
                [148, 92, "LB"], [180, 92, "MLB"], [212, 92, "LB"],
                [46, 100, "CB"], [316, 100, "CB"],
                [122, 48, "S"], [238, 48, "S"],
            ],
            "routes": [
                {"pts": [[180, 88], [180, 56]], "kind": "drop"},
                {"pts": [[144, 118], [154, 144]], "kind": "blitz"},
                {"pts": [[216, 118], [206, 144]], "kind": "blitz"},
            ],
            "zones": [
                {"cx": 106, "cy": 42, "rx": 78, "ry": 26, "lbl": "Deep 1/2"},
                {"cx": 254, "cy": 42, "rx": 78, "ry": 26, "lbl": "Deep 1/2"},
                {"cx": 54, "cy": 96, "rx": 34, "ry": 16, "lbl": "Flat"},
                {"cx": 306, "cy": 96, "rx": 34, "ry": 16, "lbl": "Flat"},
            ],
        },
    },
    "Stacked-Box Run Defense": {
        "side": "defense",
        "tagline": "Loads 7–8 defenders near the line to erase the run game and force the opponent to pass.",
        "entails": (
            "Drops the strong safety down into the box alongside four defensive linemen and three linebackers, leaving no unblocked gaps "
            "for the running back. It intentionally dares the opponent to beat 1-on-1 outside coverage through the air."
        ),
        "example": (
            "On 1st-and-10, the strong safety creeps down outside the tight end to give the defense an 8-man box against a run-heavy formation. "
            "When the offense hands off to the weak side, the unblocked backside linebacker scrapes cleanly over the top and drops the back for a 2-yard loss, "
            "setting up 2nd-and-12."
        ),
        "works_when": "The front stuffs early-down runs for minimal gain and forces uncomfortable passing downs.",
        "counter": "Hit quick play-action passes over the middle and throw 1-on-1 fades or slants against isolated outside corners.",
        "formation": "8-Man Box (4-3 Over / Strong Safety Down) · Run-Force Front",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [138, 114, "DE"], [164, 114, "DT"], [192, 114, "DT"], [218, 114, "DE"],
                [146, 94, "LB"], [180, 92, "MLB"], [216, 94, "LB"], [246, 102, "SS"],
                [46, 102, "CB"], [316, 102, "CB"],
                [180, 44, "FS"],
            ],
            "routes": [
                {"pts": [[164, 118], [164, 134]], "kind": "blitz"},
                {"pts": [[192, 118], [192, 134]], "kind": "blitz"},
                {"pts": [[246, 106], [242, 128]], "kind": "blitz"},
            ],
            "zones": [
                {"cx": 192, "cy": 104, "rx": 78, "ry": 22, "lbl": "8-Man Box"},
                {"cx": 180, "cy": 42, "rx": 110, "ry": 20, "lbl": "Single-High"},
            ],
        },
    },
    "Nickel / Light-Box Coverage": {
        "side": "defense",
        "tagline": "Puts five defensive backs on the field with a six-man box to blanket modern passing attacks.",
        "entails": (
            "Replaces a third linebacker with a fast nickel cornerback and keeps two safeties high, prioritizing coverage speed "
            "over bulk in the run box. It invites offenses to run into a 6-man front rather than giving up explosive passing plays."
        ),
        "example": (
            "Against a 3-receiver spread set, the nickel corner mirrors the slot receiver underneath while both safeties cap the seams. "
            "Every primary passing window is crowded, forcing the offense either to check down or hand the ball off into a lighter box."
        ),
        "works_when": "The 4-man defensive line holds its own against the run so the 5 defensive backs can shut down the air attack.",
        "counter": "Stay committed to downhill rushing with 6+ yards per carry until the defense is forced to drop a safety into the box.",
        "formation": "4-2-5 Nickel Two-High · 5 DBs in Coverage, 6-Man Box",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [146, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [214, 114, "DE"],
                [158, 94, "LB"], [202, 94, "LB"],
                [46, 98, "CB"], [274, 98, "NB"], [318, 98, "CB"],
                [124, 48, "S"], [236, 48, "S"],
            ],
            "routes": [
                {"pts": [[274, 94], [274, 74]], "kind": "drop"},
                {"pts": [[158, 90], [148, 76]], "kind": "drop"},
                {"pts": [[202, 90], [212, 76]], "kind": "drop"},
            ],
            "zones": [
                {"cx": 116, "cy": 46, "rx": 70, "ry": 24, "lbl": "2-High"},
                {"cx": 244, "cy": 46, "rx": 70, "ry": 24, "lbl": "2-High"},
                {"cx": 274, "cy": 84, "rx": 34, "ry": 16, "lbl": "Nickel Match"},
            ],
        },
    },
    "Pass-Rush / Front-Four Pressure": {
        "side": "defense",
        "tagline": "Generates pocket collapse with just four linemen and stunts while dropping seven into coverage.",
        "entails": (
            "The gold standard of NFL defense: wide-aligned edge rushers and twisting interior tackles (T-E stunts) win 1-on-1 blocks "
            "without needing to blitz, allowing seven defenders to stay back in tight coverage lanes."
        ),
        "example": (
            "On 3rd-and-8, the defense aligns in a Wide-9 pass-rush front and runs a tackle-end twist on the left side. "
            "The defensive tackle crashes hard into the tackle to pick him, freeing the edge rusher to loop cleanly through the B-gap for a sack "
            "while seven defenders smother every receiver downfield."
        ),
        "works_when": "The front four wins pass-rush reps cleanly without sacrificing coverage numbers.",
        "counter": "Use quick-game throws, screens, chip-blocks from tight ends/backs, and runs right at wide-aligned edge rushers.",
        "formation": "Wide-9 / 4-Man Rush · T-E Stunt with 7 in Coverage",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [126, 114, "DE"], [166, 114, "DT"], [194, 114, "DT"], [234, 114, "DE"],
                [154, 90, "LB"], [206, 90, "LB"],
                [46, 94, "CB"], [276, 94, "NB"], [318, 94, "CB"],
                [128, 48, "S"], [232, 48, "S"],
            ],
            "routes": [
                {"pts": [[166, 118], [148, 134], [146, 146]], "kind": "blitz"},
                {"pts": [[126, 118], [142, 128], [164, 142], [174, 150]], "kind": "blitz"},
                {"pts": [[194, 118], [190, 144]], "kind": "blitz"},
                {"pts": [[234, 118], [220, 146]], "kind": "blitz"},
            ],
            "zones": [
                {"cx": 180, "cy": 54, "rx": 146, "ry": 34, "lbl": "7 Defenders in Coverage"},
            ],
        },
    },
    "Bend-Don't-Break Zone": {
        "side": "defense",
        "tagline": "Soft four-deep zone shell that concedes short yards to protect against touchdowns and big plays.",
        "entails": (
            "Plays conservative Quarters (Cover 4) or soft zone spacing so four defensive backs stay deeper than the deepest receiver. "
            "It accepts 5-yard completions between the 20s, betting the offense will eventually stall or settle for a field goal once the field shrinks in the red zone."
        ),
        "example": (
            "As the offense crosses midfield, both corners and both safeties cushion back into four deep quarters. "
            "The quarterback completes three short passes to reach the 18-yard line, but once the end zone squeezes the space behind the defenders, "
            "throwing windows vanish and the drive ends in a field goal."
        ),
        "works_when": "The defense avoids busts, tackles in bounds, and holds opponents to field goals in the red zone.",
        "counter": "Stay patient with methodical underneath drives, win 3rd-and-short, and punch in red-zone touchdowns with physical runs or pick plays.",
        "formation": "Cover 4 / Soft Quarters · Four Deep Zones + Rally Tackling",
        "diagram": {
            "off": REF_OFF_11,
            "def": [
                [144, 114, "DE"], [168, 114, "DT"], [192, 114, "DT"], [216, 114, "DE"],
                [148, 92, "LB"], [180, 90, "MLB"], [212, 92, "LB"],
                [48, 86, "CB"], [312, 86, "CB"],
                [128, 56, "S"], [232, 56, "S"],
            ],
            "routes": [
                {"pts": [[48, 82], [50, 44]], "kind": "drop"},
                {"pts": [[312, 82], [310, 44]], "kind": "drop"},
                {"pts": [[128, 54], [132, 38]], "kind": "drop"},
                {"pts": [[232, 54], [228, 38]], "kind": "drop"},
            ],
            "zones": [
                {"cx": 56, "cy": 42, "rx": 40, "ry": 24, "lbl": "1/4"},
                {"cx": 138, "cy": 42, "rx": 40, "ry": 24, "lbl": "1/4"},
                {"cx": 222, "cy": 42, "rx": 40, "ry": 24, "lbl": "1/4"},
                {"cx": 304, "cy": 42, "rx": 40, "ry": 24, "lbl": "1/4"},
            ],
        },
    },
}
