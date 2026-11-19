"""HTML for ddyno pages. Plain strings, no build step.

One visual language for every page: dark surface, row-based lists, right-aligned tabular numbers,
tinted change pills, hairline borders. Tokens live in :root. Pages only read the existing API."""

FIGJS = r"""/* Sideline: Stardew-inspired pixel vignettes, one per current league leader.
   Generic football players (full pads, helmet, jersey number) and coaches in varied environments. */
const Sideline=(()=>{
  const NS='http://www.w3.org/2000/svg';
  const S=(n,at)=>{const e=document.createElementNS(NS,n);for(const k in at)e.setAttribute(k,at[k]);return e};
  /* team: [jersey, trim, helmet, pants] */
  const TEAM={ARI:['#97233f','#ffffff','#ffffff','#ffffff'],ATL:['#101820','#a71930','#101820','#ffffff'],BAL:['#241773','#9e7c0c','#16101f','#ffffff'],BUF:['#00338d','#c60c30','#ffffff','#ffffff'],
    CAR:['#101820','#0085ca','#bfc0bf','#bfc0bf'],CHI:['#0b162a','#c83803','#0b162a','#ffffff'],CIN:['#101820','#fb4f14','#fb4f14','#ffffff'],CLE:['#311d00','#ff3c00','#ff3c00','#ffffff'],
    DAL:['#003594','#869397','#869397','#869397'],DEN:['#fb4f14','#002244','#002244','#ffffff'],DET:['#0076b6','#b0b7bc','#b0b7bc','#b0b7bc'],GB:['#203731','#ffb612','#ffb612','#ffb612'],
    HOU:['#03202f','#a71930','#03202f','#ffffff'],IND:['#002c5f','#ffffff','#ffffff','#ffffff'],JAX:['#006778','#d7a22a','#101820','#ffffff'],KC:['#e31837','#ffb81c','#e31837','#ffffff'],
    LV:['#101820','#a5acaf','#a5acaf','#a5acaf'],LAC:['#0080c6','#ffc20e','#ffffff','#ffc20e'],LA:['#003594','#ffd100','#003594','#ffd100'],MIA:['#008e97','#fc4c02','#ffffff','#ffffff'],
    MIN:['#4f2683','#ffc62f','#4f2683','#ffffff'],NE:['#002244','#c60c30','#b0b7bc','#b0b7bc'],NO:['#101820','#d3bc8d','#d3bc8d','#d3bc8d'],NYG:['#0b2265','#a71930','#0b2265','#a5acaf'],
    NYJ:['#125740','#ffffff','#125740','#ffffff'],PHI:['#004c54','#a5acaf','#004c54','#ffffff'],PIT:['#101820','#ffb612','#101820','#ffb612'],SF:['#aa0000','#b3995d','#b3995d','#b3995d'],
    SEA:['#002244','#69be28','#002244','#a5acaf'],TB:['#d50a0a','#ff7900','#5a544d','#5a544d'],TEN:['#0c2340','#4b92db','#0c2340','#ffffff'],WAS:['#5a1414','#ffb612','#5a1414','#ffb612']};
  const rgb=h=>[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];
  const hex=a=>'#'+a.map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');
  /* Stardew hue-shifting: warm sunlight highlights, rich plum/espresso shadows */
  const mix=(a,b,t)=>{const A=rgb(a),B=rgb(b);return hex([A[0]+(B[0]-A[0])*t,A[1]+(B[1]-A[1])*t,A[2]+(B[2]-A[2])*t])};
  const luma=h=>{const c=rgb(h);return .299*c[0]+.587*c[1]+.114*c[2]};
  const hash=s=>{let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return Math.abs(h)};
  const R=(g,x,y,w,h,f,op)=>{const at={x,y,width:w,height:h,fill:f};if(op!=null)at.opacity=op;g.appendChild(S('rect',at))};
  const paint=(g,rows,x0,y0,pal)=>rows.forEach((r,y)=>{let x=0;while(x<r.length){const c=r[x];if(c==='.'){x++;continue}
    let n=1;while(r[x+n]===c)n++;R(g,x0+x,y0+y,n,1,pal[c]||'#f0f');x+=n}});

  /* 3x5 pixel digits for jersey chest numbers */
  const DIG={
    0:['111','101','101','101','111'],1:['010','110','010','010','111'],2:['111','001','111','100','111'],
    3:['111','001','111','001','111'],4:['101','101','111','001','001'],5:['111','100','111','001','111'],
    6:['111','100','111','101','111'],7:['111','001','001','010','010'],8:['111','101','111','101','111'],
    9:['111','101','111','001','111']
  };
  const drawNum=(g,num,x0,y0,col)=>{
    const ds=String(num||'').replace(/\D/g,'').slice(0,2);if(!ds)return;
    const sx=ds.length===1?x0+7:x0+5;
    for(let k=0;k<ds.length;k++){const bm=DIG[ds[k]];if(!bm)continue;
      bm.forEach((row,ry)=>{for(let rx=0;rx<3;rx++)if(row[rx]==='1')R(g,sx+k*4+rx,y0+ry,1,1,col)})}
  };

  /* 17x22 football player in full equipment (helmet, facemask, bulky shoulder pads, pants, knee pads, cleats) */
  const PLAYER=[
    "....OOOOOOOOO....",
    "...OIIHHSHHDDO...",
    "..OIIHHHSHHHDDO..",
    "..OHHHHHSHHHDDO..",
    "..OHHKEKKKEKDDO..",
    "..OHMKMKMKMKMDO..",
    "...OOMMMMMMMOO...",
    "..OOOOOWWWOOOOO..",
    "OLTLLJJJJJJJYYTYO",
    "OJTOJJJJJJJJYOTYO",
    "OJJOJJJJJJJJYOYYO",
    "OKKOJJJJJJJJYOKKO",
    "OGGOJJJJJJJJYOGGO",
    ".OOOJJJJJJJJYOOO.",
    "...OJJJJJJJJYO...",
    "...OTTTTTTTTTO...",
    "...OTPPPPPRRTO...",
    "...OPQQPOPQQRO...",
    "....OPPO.OPRO....",
    "....OTTO.OTTO....",
    "....OWWO.OWWO....",
    "...OCCCO.OCCCO..."
  ];
  const PLAYER_SIT=[
    ...PLAYER.slice(0,16),
    "...OTPPPPPRRTO...",
    "..OQPPO...OPQRO..",
    "..OTTO.....OTTO..",
    "..OWWO.....OWWO..",
    ".OCCCO.....OCCCO.",
    "................."
  ];
  /* 17x22 Stardew-style coaches (cap or hair, headset, warm rosy cheeks, quarter-zip, khakis) */
  const COACH_CAP=[
    "....OOOOOOOOO....",
    "...OJJJTTTJJYO...",
    "...OJJJJJJJYYO...",
    "..OOTTTTTTTTTOO..",
    "..EOKKKKKKKKKOE..",
    "..EOKKEKKKEKKOE..",
    "..EOKcKKKKKcKOE..",
    "...OKKKKKKKKMO...",
    "....OOKKKKMMO....",
    "..OOOJJWWWYYOOO..",
    ".OJJJJJTWTJJJYYO.",
    ".OJJOJJJTJJYOYYO.",
    ".OKKOJJJTJJYOKKO.",
    ".OKKOJJJJJJYOKKO.",
    "..OO.OJJJJYO.OO..",
    "....OQQQQQQZO....",
    "....OQQQQQQZO....",
    "....OQQQOQQZO....",
    "....OQQO.OQZO....",
    "....OQQO.OQZO....",
    "....OWWO.OWWO....",
    "...OCCCO.OCCCO..."
  ];
  const COACH_HAIR=[
    "....OOOOOOOOO....",
    "...OhiihhhhhdO...",
    "..OhihhhhhhhddO..",
    "..EOhhhhhhhhdOE..",
    "..EOKKKKKKKKKOE..",
    "..EOKKEKKKEKKOE..",
    "..EOKcKKKKKcKOE..",
    "...OKKKKKKKKMO...",
    "....OOKKKKMMO....",
    ...COACH_CAP.slice(9)
  ];

  const BALL=['.OOO.','OBBLO','ODDBO','.OOO.'];
  const BOARD=['OOOOO','OAAAO','OUUUO','OUUUO','OUUUO','OOOOO'];
  const MUG=['OOO.','OWWO','OWWO','OOO.'];
  const STEAM=['.w.','w..','.w.'];
  const HAIR=[['#5c3a21','#7b5132','#3e2514'],['#8f5b2c','#b57941','#663e1c'],['#3a3136','#574b52','#231d21'],['#8c8881','#b3aea6','#66625c']];

  const SCENE_META={
    office:"Coach's office",stadium:'Stadium sideline',film_room:'Film room',tunnel:'Stadium concourse',
    field:'Under the lights',practice:'Practice field',locker_room:'Locker room',sideline_bench:'Sideline bench',gym:'Weight room',tunnel_run:'Stadium tunnel'
  };
  const COACH_SCENES=['office','stadium','film_room','tunnel'];
  const PLAYER_SCENES=['field','practice','locker_room','sideline_bench','gym','tunnel_run'];
  const GROUP_SCENES={
    coach_afc:['office','stadium'],coach_nfc:['film_room','tunnel'],
    qbr:['field','practice'],pass_td:['tunnel_run','sideline_bench'],
    ypc:['field','practice','locker_room'],rec_yds:['field','practice','sideline_bench'],
    rec_td:['tunnel_run','field','locker_room'],sacks:['gym','field'],tackles:['locker_room','practice']
  };

  /* 44x32 Stardew-inspired miniature environments (back + optional foreground overlay) */
  function drawScene(bg,fg,scene,teamCol,trimCol,idx){
    const W=44,H=32;
    if(scene==='office'){
      /* Cozy Stardew cedar-plank coach's office with window, chalkboard, fern, desk & steaming mug */
      R(bg,0,0,W,23,'#b67b4b');
      for(let y=3;y<22;y+=4)R(bg,0,y,W,1,'#9e6338');
      for(let y=0;y<22;y+=4){R(bg,10+(y%8),y,1,3,'#a76b3e');R(bg,29-(y%8),y,1,3,'#a76b3e')}
      R(bg,0,22,W,2,'#6e4124');R(bg,0,24,W,8,'#8c5834');
      /* sunlit window (left) */
      R(bg,2,3,10,9,'#5c341d');R(bg,3,4,8,7,'#88d1ec');R(bg,3,8,8,3,'#bce8f7');
      R(bg,4,5,3,1,'#faf6ea');R(bg,5,4,2,1,'#ffffff');
      R(bg,6,4,1,7,'#734427');R(bg,3,7,8,1,'#734427');
      /* chalkboard with X's and O's (right) */
      R(bg,29,3,13,9,'#6b3e22');R(bg,30,4,11,7,'#2d523c');R(bg,30,10,11,1,'#244331');
      R(bg,32,6,1,1,'#f4f0df');R(bg,34,6,1,1,'#f4f0df');R(bg,33,7,1,1,'#f4f0df');
      R(bg,32,8,1,1,'#f4f0df');R(bg,34,8,1,1,'#f4f0df');
      R(bg,37,6,2,1,'#ffd972');R(bg,39,5,1,2,'#ffd972');R(bg,36,8,3,1,'#f4f0df');
      /* potted Stardew fern (far left) */
      R(bg,2,17,4,5,'#c76b44');R(bg,2,17,4,1,'#db8358');R(bg,3,18,2,4,'#a85432');
      R(bg,1,14,6,3,'#4a9b43');R(bg,2,13,4,2,'#6bc256');R(bg,3,12,2,1,'#8bd96c');
      /* office chair backrest behind coach */
      R(bg,16,13,12,10,'#3b2a26');R(bg,17,14,10,8,'#56403a');R(bg,18,14,8,2,'#6b5149');
      /* Foreground oak desk + open playbook + warm lamp + steaming coffee mug */
      R(fg,7,23,30,9,'#704224');R(fg,8,24,28,2,'#d49a64');R(fg,8,26,28,5,'#a66a3c');
      R(fg,9,27,26,1,'#8f572e');R(fg,10,28,9,2,'#824d27');R(fg,25,28,9,2,'#824d27');
      R(fg,14,29,1,1,'#e6c36a');R(fg,29,29,1,1,'#e6c36a');
      /* open playbook on desk */
      R(fg,17,23,10,3,'#f6f1e1');R(fg,22,23,1,3,'#c9bfa6');
      R(fg,18,24,3,1,'#5282c2');R(fg,24,24,2,1,'#c7584a');
      /* desk lamp (left of desk) */
      R(fg,9,23,3,1,'#4d3b32');R(fg,10,20,1,3,'#7a685c');R(fg,8,19,5,2,'#e8b84b');R(fg,9,21,3,1,'#fff4b8',0.6);
      /* coffee mug + animated steam (right of desk) */
      R(fg,31,21,3,3,'#f4eee0');R(fg,34,22,1,1,'#f4eee0');R(fg,32,21,1,1,'#6e4326');
      const st=S('g',{'class':'px-steam'});st.style.animationDelay=(-idx*.7)+'s';
      R(st,32,19,1,1,'#ffffff',0.8);R(st,31,17,1,1,'#ffffff',0.55);R(st,33,15,1,1,'#ffffff',0.35);
      fg.appendChild(st);
    }else if(scene==='stadium'){
      /* Sunlit Stardew stadium: blue sky, fluffy cloud, bleachers with fans, goalpost, lush grass */
      R(bg,0,0,W,11,'#7bc7e6');R(bg,0,7,W,4,'#a6ddf2');
      R(bg,5,2,7,2,'#ffffff');R(bg,6,1,5,1,'#ffffff');R(bg,26,3,6,2,'#ffffff');R(bg,27,2,4,1,'#ffffff');
      /* bleachers & colorful pixel crowd */
      R(bg,0,10,W,9,'#586375');R(bg,0,11,W,1,'#717e94');R(bg,0,14,W,1,'#717e94');R(bg,0,17,W,2,'#3f4857');
      const fans=['#e05a47','#f2c14e','#55a6e0','#f4f1e6',teamCol,trimCol];
      for(let x=2;x<W-1;x+=3){R(bg,x,10,2,1,fans[(x+idx)%fans.length]);R(bg,x+1,13,2,1,fans[(x*2+idx)%fans.length])}
      /* yellow goalpost upright (right) */
      R(bg,36,3,1,10,'#f2c84b');R(bg,40,3,1,10,'#f2c84b');R(bg,36,12,5,1,'#f2c84b');R(bg,38,13,1,6,'#d9ad38');
      /* sideline wall & Stardew grass turf */
      R(bg,0,19,W,2,teamCol);R(bg,0,19,W,1,mix(teamCol,'#fff4d1',.2));
      R(bg,0,21,W,11,'#58a642');R(bg,0,25,W,1,'#f4f1e6');R(bg,0,30,W,2,'#468c34');
      for(let x=3;x<W;x+=7){R(bg,x,22,1,2,'#74c257');R(bg,x+1,23,1,1,'#74c257');R(bg,x+3,28,2,1,'#499137')}
      /* orange yard marker */
      R(bg,4,21,3,4,'#f07b30');R(bg,5,22,1,2,'#fff6e5');
    }else if(scene==='film_room'){
      /* Cozy dark-wood & slate film room with glowing play-diagram screen & playbook shelf */
      R(bg,0,0,W,23,'#3e3647');R(bg,0,0,W,2,'#5e3e28');
      for(let y=4;y<22;y+=4)R(bg,0,y,W,1,'#342d3d');
      R(bg,0,22,W,2,'#6e4326');R(bg,0,24,W,8,'#8f5b37');
      for(let x=0;x<W;x+=8)R(bg,x,24,1,8,'#784a2b');
      /* glowing projector screen with mini football field & play routes */
      R(bg,3,4,19,13,'#6b4227');R(bg,4,5,17,11,'#1e2924');
      const scr=S('g',{'class':'px-glow'});
      R(scr,5,6,15,9,'#2f6b3e');
      for(let x=8;x<=16;x+=4)R(scr,x,6,1,9,'#458a54');
      R(scr,7,11,1,1,'#fff3b0');R(scr,10,12,1,1,'#fff3b0');R(scr,13,11,1,1,'#fff3b0');
      R(scr,7,8,1,3,'#ffffff');R(scr,8,8,3,1,'#ffffff');R(scr,13,9,4,1,'#ff9472');R(scr,16,8,1,1,'#ff9472');
      bg.appendChild(scr);
      /* bookshelf of playbooks (right) */
      R(bg,33,6,9,16,'#6e4124');R(bg,34,7,7,4,'#4d2c17');R(bg,34,12,7,4,'#4d2c17');R(bg,34,17,7,4,'#4d2c17');
      R(bg,35,8,2,3,teamCol);R(bg,37,8,2,3,'#e0b44c');R(bg,39,9,1,2,'#d95c4a');
      R(bg,35,13,2,3,'#589cd6');R(bg,38,13,2,3,trimCol);R(bg,35,18,3,3,'#78b863');
    }else if(scene==='tunnel'){
      /* Stadium tunnel concourse: warm brick archway, sunlit sky + floodlights, team banner, cooler */
      R(bg,0,0,W,22,'#8a7565');
      for(let y=2;y<22;y+=3){R(bg,0,y,W,1,'#756153');for(let x=(y%6?3:0);x<W;x+=6)R(bg,x,y-2,1,2,'#756153')}
      /* bright arched stadium opening */
      R(bg,13,3,18,19,'#54443a');R(bg,14,4,16,18,'#8ad2ed');R(bg,14,12,16,10,'#b5e5f7');
      R(bg,16,6,2,6,'#525c6b');R(bg,15,5,4,2,'#fff5c2');
      R(bg,26,6,2,6,'#525c6b');R(bg,25,5,4,2,'#fff5c2');
      R(bg,14,17,16,5,'#5aa643');R(bg,14,19,16,1,'#f4f1e6');
      /* team pennant banner on left wall */
      R(bg,3,5,7,9,teamCol);R(bg,3,5,7,1,'#d4a24c');R(bg,4,8,5,2,trimCol);R(bg,3,13,2,1,'#8a7565');R(bg,8,13,2,1,'#8a7565');
      /* concrete concourse floor */
      R(bg,0,22,W,10,'#9e958b');R(bg,0,22,W,1,'#bdb4aa');R(bg,0,30,W,2,'#7d756c');
      /* Gatorade cooler on right */
      R(bg,35,18,6,7,'#eb7228');R(bg,35,17,6,2,'#f7f3e8');R(bg,37,22,2,2,'#3d3530');
    }else if(scene==='field'){
      /* Under the stadium lights: twilight sky, glowing floodlights, Stardew grass, yard lines, pylon */
      R(bg,0,0,W,13,'#273859');R(bg,0,6,W,5,'#39507a');R(bg,0,10,W,3,'#586e96');
      /* two stadium light towers */
      for(const lx of [6,34]){
        R(bg,lx+1,6,2,8,'#434f66');R(bg,lx,2,4,4,'#606e87');
        const gl=S('g',{'class':'px-glow'});R(gl,lx,2,4,3,'#fff4b8');R(gl,lx-1,1,6,5,'#fff4b8',0.22);bg.appendChild(gl);
      }
      /* distant stands & wall */
      R(bg,0,13,W,5,'#323c4f');R(bg,0,18,W,2,teamCol);
      for(let x=2;x<W;x+=4)R(bg,x,14,2,1,(x%8)?'#7a88a3':trimCol);
      /* lush Stardew turf + yard line + orange pylon */
      R(bg,0,20,W,12,'#499439');R(bg,0,20,W,1,'#5cb048');R(bg,0,30,W,2,'#3a7a2d');
      R(bg,0,26,W,1,'#f4f1e6');R(bg,10,20,1,12,'#f4f1e6',0.45);R(bg,33,20,1,12,'#f4f1e6',0.45);
      for(let x=4;x<W;x+=6){R(bg,x,22,1,2,'#62b54c');R(bg,x+2,28,1,1,'#3c802f')}
      R(bg,37,20,3,6,'#ff6e26');R(bg,38,20,1,5,'#ff9a52');
    }else if(scene==='practice'){
      /* Sunny Stardew training camp: sky, clouds, pine treeline, emerald turf, cones & blocking pad */
      R(bg,0,0,W,13,'#79c8ea');R(bg,0,8,W,5,'#aee0f5');
      R(bg,4,2,7,2,'#ffffff');R(bg,6,1,4,1,'#ffffff');R(bg,30,3,6,2,'#ffffff');
      /* classic Stardew pine treeline */
      for(let tx=0;tx<W;tx+=7){
        R(bg,tx+2,9,3,3,'#2f6939');R(bg,tx+1,11,5,4,'#3c7d44');R(bg,tx,14,7,4,'#2f6939');R(bg,tx+3,12,1,2,'#549e56');
      }
      R(bg,0,18,W,2,'#7c6148');R(bg,0,19,W,1,'#a38262');
      /* sunny practice turf */
      R(bg,0,20,W,12,'#64b347');R(bg,0,30,W,2,'#4e9637');
      for(let x=2;x<W;x+=5){R(bg,x,22,1,2,'#82cc5e');R(bg,x+2,27,1,1,'#539c3a')}
      /* orange agility cones (left) */
      R(bg,4,26,4,1,'#d9581a');R(bg,5,24,2,2,'#ff7729');R(bg,5,25,2,1,'#fff4e0');
      R(bg,9,24,3,1,'#d9581a');R(bg,10,22,1,2,'#ff7729');
      /* blue/gold blocking dummy (right) */
      R(bg,35,16,5,11,'#2c4e82');R(bg,36,16,3,10,'#3e69a8');R(bg,35,20,5,2,'#f2c14e');R(bg,34,26,7,2,'#26374d');
    }else if(scene==='locker_room'){
      /* Stardew carpenter-wood locker cubbies with vents, shelf gear, team header & bench */
      R(bg,0,0,W,24,'#a86d3f');R(bg,0,0,W,3,'#6e4124');R(bg,0,3,W,1,teamCol);
      for(const lx of [1,12,23,34]){
        R(bg,lx,4,10,19,'#754526');R(bg,lx+1,5,8,17,'#bf8452');
        R(bg,lx+2,6,6,2,teamCol);R(bg,lx+3,6,4,1,trimCol);
        R(bg,lx+2,10,6,1,'#87522e');R(bg,lx+2,12,6,1,'#87522e');
        R(bg,lx+2,16,6,5,'#9c6438');
      }
      /* towel & mini ball in lockers */
      R(bg,4,17,4,3,'#f5f1e4');R(bg,37,18,3,2,'#9c5528');
      /* tiled/carpet floor + wooden bench */
      R(bg,0,23,W,9,'#4b5363');for(let x=0;x<W;x+=6)R(bg,x,23,1,9,'#3f4654');
      R(bg,4,25,36,2,'#d49b63');R(bg,4,27,36,1,'#8f5931');R(bg,7,28,2,3,'#613a1f');R(bg,35,28,2,3,'#613a1f');
    }else if(scene==='sideline_bench'){
      /* Sideline bench & orange Gatorade jug, stadium crowd behind, lush turf */
      R(bg,0,0,W,12,'#7fc8e6');R(bg,0,7,W,5,'#acdcf0');
      R(bg,0,10,W,7,'#4d5769');
      const fans=['#e05a47','#f2c14e','#55a6e0','#f4f1e6',teamCol,trimCol];
      for(let x=1;x<W-1;x+=3){R(bg,x,11,2,1,fans[(x+idx)%fans.length]);R(bg,x+1,14,2,1,fans[(x+2+idx)%fans.length])}
      R(bg,0,17,W,2,teamCol);R(bg,0,19,W,13,'#58a642');R(bg,0,30,W,2,'#468c34');
      for(let x=3;x<W;x+=7)R(bg,x,28,2,1,'#74c257');
      /* bench behind/under seated player */
      R(bg,10,22,28,2,'#c8cfd6');R(bg,10,24,28,1,'#8e98a3');R(bg,12,25,2,5,'#646e7a');R(bg,34,25,2,5,'#646e7a');
      R(bg,32,22,4,4,'#f6f3e8');/* sideline towel draped on bench */
      /* Gatorade cooler on left */
      R(bg,2,19,7,8,'#eb7228');R(bg,2,18,7,2,'#f7f3e8');R(bg,3,20,5,1,'#ff964f');R(bg,4,24,2,2,'#3b332d');
      R(bg,5,16,2,2,'#e3f2fd');/* cup stack */
    }else if(scene==='gym'){
      /* Training facility / weight room: warm brick wall, window, barbell rack, pennant, rubber mat */
      R(bg,0,0,W,22,'#965744');
      for(let y=2;y<22;y+=3){R(bg,0,y,W,1,'#7d4535');for(let x=(y%6?3:0);x<W;x+=6)R(bg,x,y-2,1,2,'#7d4535')}
      /* high sunlit window (left) */
      R(bg,2,3,11,7,'#573526');R(bg,3,4,9,5,'#9cdaf0');R(bg,7,4,1,5,'#573526');
      /* team pennant (center-left) */
      R(bg,15,2,8,4,teamCol);R(bg,16,3,5,2,trimCol);R(bg,22,2,1,1,'#965744');R(bg,22,5,1,1,'#965744');
      /* barbell squat rack (right) */
      R(bg,31,7,1,16,'#3d434d');R(bg,40,7,1,16,'#3d434d');R(bg,30,11,12,1,'#b8c0cc');
      R(bg,29,9,2,5,'#2a2f38');R(bg,41,9,2,5,'#2a2f38');R(bg,30,10,1,3,teamCol);R(bg,41,10,1,3,teamCol);
      /* gym floor + kettlebell */
      R(bg,0,22,W,10,'#454954');R(bg,0,22,W,1,'#5f6573');
      for(let x=2;x<W;x+=8)R(bg,x,25,2,1,'#535866');
      R(bg,5,24,3,3,'#252930');R(bg,6,23,1,1,'#596170');
    }else{
      /* tunnel_run: dramatic brick & steel stadium tunnel opening onto bright floodlit field + mist */
      R(bg,0,0,W,22,'#4a4146');R(bg,0,0,W,4,'#383136');
      R(bg,8,4,28,18,'#2a2429');R(bg,10,6,24,16,'#3d4a66');R(bg,12,8,20,14,'#6d82ab');
      /* overhead tunnel lamps + team banner */
      R(bg,14,1,16,3,teamCol);R(bg,16,2,12,1,trimCol);
      const gl=S('g',{'class':'px-glow'});
      R(gl,13,6,4,2,'#fff3b0');R(gl,27,6,4,2,'#fff3b0');R(gl,12,8,20,6,'#fff4c2',0.16);
      bg.appendChild(gl);
      /* turf carpet leading out */
      R(bg,0,22,W,10,'#468c36');R(bg,10,22,24,10,'#59a844');R(bg,10,22,1,10,'#f4f1e6');R(bg,33,22,1,10,'#f4f1e6');
      /* animated game-day smoke/sparkle motes */
      const sm=S('g',{'class':'px-steam'});sm.style.animationDelay=(-idx*.8)+'s';
      R(sm,8,20,2,2,'#ffffff',0.4);R(sm,34,19,2,2,'#ffffff',0.4);R(sm,10,16,1,1,'#fff4c2',0.55);R(sm,33,15,1,1,'#fff4c2',0.55);
      fg.appendChild(sm);
    }
  }

  function sprite(role,team,i,opts){
    opts=opts||{};
    const t=TEAM[team]||['#2f6bb8','#f2c14e','#2f6bb8','#f4f1e6'];
    const coach=role==='coach',num=opts.number||'',name=opts.name||'';
    const scene=opts.scene||(coach?COACH_SCENES[i%COACH_SCENES.length]:PLAYER_SCENES[i%PLAYER_SCENES.length]);
    const seated=(coach&&scene==='office')||(!coach&&scene==='sideline_bench');
    const darkOut='#321d18';
    const jersey=t[0],trim=t[1],helm=t[2],pants=t[3];
    const numCol=luma(jersey)>175?(luma(trim)<120?trim:darkOut):'#faf6e8';
    const hair=HAIR[hash(name||team)%HAIR.length];
    const pal={
      O:darkOut,H:helm,I:mix(helm,'#fff8dc',.42),D:mix(helm,'#2a1826',.35),S:trim,
      J:jersey,L:mix(jersey,'#fff6d6',.28),Y:mix(jersey,'#2a1826',.32),T:trim,
      P:pants,R:mix(pants,'#2a1826',.28),Q:mix(pants,'#ffffff',.4),
      K:'#f0be96',c:'#e38b79',E:'#2d1a16',M:'#c6ccd4',V:'#1c2738',v:'#7ab8e8',
      W:'#faf6eb',G:role==='wr'?trim:'#eef1f4',C:'#362826',
      B:'#a85d2e',A:'#8a6f52',U:'#f6f1e1',Q2:'#c9b288',Z:'#a38b62',
      h:hair[0],i:hair[1],d:hair[2]
    };
    if(coach){pal.Q='#cbb48a';pal.Z='#a38c64';pal.E='#2e3138'}
    if(pal.S.toLowerCase()===pal.H.toLowerCase())pal.S=mix(pal.H,'#2a1826',.38);
    if(pal.T.toLowerCase()===pal.J.toLowerCase())pal.T='#faf6eb';

    const svg=S('svg',{viewBox:'0 0 44 32','class':'px',width:88,height:64,'shape-rendering':'crispEdges','aria-hidden':'true'});
    const bg=S('g',{}),fg=S('g',{});
    drawScene(bg,fg,scene,jersey,trim,i);
    svg.appendChild(bg);

    /* ground shadow under standing character */
    const cx=coach&&scene==='film_room'?18:13;
    const cy=seated?(coach?6:7):8;
    if(!seated)R(svg,cx+3,cy+21,11,2,'#1b1214',0.28);

    let base;
    if(coach){
      base=(hash(name+team)%2===0?COACH_CAP:COACH_HAIR).map(r=>r.split(''));
      if(scene==='office')base=base.slice(0,15);/* seated behind desk */
    }else{
      base=(seated?PLAYER_SIT:PLAYER).map(r=>r.split(''));
    }
    const put=(x,y,str)=>{if(!base[y])return;str.split('').forEach((ch,k)=>{if(ch!=='.'&&base[y][x+k]!=null)base[y][x+k]=ch})};

    if(!coach){
      /* Position equipment customization */
      const visor=role==='rush'||role==='rb'||(role==='wr'&&hash(name)%2===0);
      if(visor){put(5,4,'VvVVVVv');put(5,5,'VMVMVMV')}
      if(role==='rush'||role==='tackle'){put(6,7,'DDDDD');put(1,11,'TT');put(14,11,'TT')}
      if(role==='qb'){put(1,11,'WW');put(4,16,'W');put(4,17,'W')}
      if(role==='rb'){put(1,11,'WW');put(14,11,'WW')}
      if(role==='wr'){put(12,16,'W');put(12,17,'W');put(12,18,'W')}
    }else if(scene==='film_room'){
      /* Coach raising left arm to hold pointer toward the film screen */
      put(0,9,'KK');put(1,10,'JJ');put(1,11,'JJ');
    }

    const chG=S('g',{}),legs=S('g',{}),up=S('g',{'class':'px-up'});
    const splitY=seated?base.length:16;
    if(!seated)paint(legs,base.slice(splitY).map(r=>r.join('')),cx,cy+splitY,pal);
    paint(up,base.slice(0,splitY).map(r=>r.join('')),cx,cy,pal);

    /* Real pixel jersey number on player chest */
    if(!coach&&num)drawNum(up,num,cx,cy+9,numCol);

    /* Props & idle animations */
    const ballPal={O:darkOut,B:'#a85d2e',D:'#753c1b',L:'#faf6eb'};
    if(!coach){
      if(role==='qb'||role==='wr'){
        const prop=S('g',{'class':'px-toss'});prop.style.animationDelay=(-i*.9)+'s';
        paint(prop,BALL,cx+14,cy+8,ballPal);up.appendChild(prop);
      }else if(role==='rb'){
        paint(up,BALL,cx+1,cy+11,ballPal);
      }
    }else if(scene==='stadium'){
      const prop=S('g',{'class':'px-tap'});prop.style.animationDelay=(-i*.8)+'s';
      paint(prop,BOARD,cx+12,cy+11,pal);up.appendChild(prop);
    }else if(scene==='tunnel'){
      paint(up,MUG,cx+13,cy+11,{O:darkOut,W:'#f4eee0'});
      R(up,cx+14,cy+11,2,1,'#6e4326');
      const st=S('g',{'class':'px-steam'});st.style.animationDelay=(-i*.6)+'s';
      paint(st,STEAM,cx+13,cy+8,{w:'#e8e0d5'});up.appendChild(st);
    }else if(scene==='film_room'){
      /* Wooden pointer held in hand reaching to the screen */
      const pt=S('g',{'class':'px-tap'});pt.style.animationDelay=(-i*.7)+'s';
      R(pt,cx-4,cy+9,5,1,'#e8c488');R(pt,cx-5,cy+9,1,1,'#ff6b57');
      up.appendChild(pt);
    }

    up.style.animationDuration=(1.35+(i%4)*.19)+'s';
    up.style.animationDelay=(-i*.43)+'s';
    chG.appendChild(legs);chG.appendChild(up);svg.appendChild(chG);
    svg.appendChild(fg);
    return svg;
  }

  const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
  function mount(box,page){
    fetch('/api/leaders?page='+encodeURIComponent(page)).then(r=>r.ok?r.json():Promise.reject()).then(d=>{
      if(!d.groups||!d.groups.length)return;box.replaceChildren();let n=0;
      d.groups.forEach(g=>{const sec=el('section','sl-g');sec.appendChild(el('h2','sl-h',g.title));
        const row=el('div','sl-row');
        const pool=g.role==='coach'?COACH_SCENES:PLAYER_SCENES;
        const picks=GROUP_SCENES[g.id]||pool;
        g.players.forEach((p,pi)=>{
          const idx=n++;
          let sc=picks[pi%picks.length];
          const c=el('figure','sl-p');
          const frame=el('button','sl-scene');frame.type='button';
          const render=()=>{
            frame.replaceChildren(sprite(g.role,p.team,idx,{number:p.number,name:p.name,scene:sc}));
            const loc=SCENE_META[sc]||'';
            const numTag=p.number?' #'+p.number:'';
            c.title=p.name+numTag+' ('+p.team+'): '+p.value+' '+g.unit+(p.detail?', '+p.detail:'')+(loc?' · '+loc:'')+' (click to change scene)';
            frame.setAttribute('aria-label',p.name+', '+loc+'. Click to switch scene.');
          };
          frame.onclick=()=>{sc=pool[(pool.indexOf(sc)+1)%pool.length];render()};
          render();
          c.appendChild(frame);
          const cap=el('figcaption');
          cap.appendChild(el('b',null,p.value));
          cap.appendChild(el('span',null,p.name));
          cap.appendChild(el('small',null,(p.number?'#'+p.number+' · ':'')+p.team));
          c.appendChild(cap);row.appendChild(c);
        });
        sec.appendChild(row);box.appendChild(sec)});
      box.appendChild(el('p','sl-note','League leaders through Week '+d.through_week+'. Click any scene to switch environments.'));
      box.hidden=false;
    }).catch(()=>{});
  }
  return {mount,sprite,TEAM,COACH_SCENES,PLAYER_SCENES};
})();
"""

CSS = """
:root{--bg:#0d1117;--card:#161b22;--raise:#1c232d;--line:#30363d;--hair:#21262d;--fg:#e6edf3;--mute:#8b949e;
--acc:#58a6ff;--up:#3fb950;--down:#f0883e;--neg:#f85149;--warn:#d29922;--ink:#04111f;
--r:14px;--r-sm:9px;--pad:20px}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--acc)}button{font:inherit;cursor:pointer;color:inherit}
h1,h2,h3,p{margin:0}
.num,.val,.pill,td,th,.big,.kv b{font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px;border-radius:6px}

/* shell */
.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;height:56px;padding:0 var(--pad);
background:rgba(13,17,23,.82);-webkit-backdrop-filter:saturate(1.4) blur(14px);backdrop-filter:saturate(1.4) blur(14px);border-bottom:1px solid var(--hair)}
.brand{font-weight:800;font-size:1.15rem;letter-spacing:-.02em;color:var(--fg);text-decoration:none;display:inline-flex;align-items:center;gap:8px;min-height:44px}
.brand i{width:10px;height:10px;border-radius:3px;background:var(--acc);display:block}
.crumb{color:var(--mute);font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.crumb:before{content:"/";margin-right:10px;color:var(--line)}
.wrap{max-width:1200px;margin:0 auto;padding:28px var(--pad) 72px}
.title{font-size:clamp(2rem,6vw,2.6rem);line-height:1.08;font-weight:800;letter-spacing:-.025em}
.title span{display:block;color:var(--mute)}
.lede{color:var(--mute);margin-top:10px;max-width:60ch}
.eyebrow{color:var(--acc);font-size:.86rem;font-weight:600;margin-bottom:6px}
.card{background:var(--card);border:1px solid var(--hair);border-radius:var(--r)}
.sech{display:flex;justify-content:space-between;align-items:baseline;gap:12px;color:var(--mute);font-size:.86rem;font-weight:600;padding:0 2px 8px}
.pill{display:inline-block;min-width:58px;padding:3px 8px;border-radius:7px;font-size:.86rem;font-weight:600;text-align:right;white-space:nowrap}
.pill.up{background:rgba(63,185,80,.16);color:var(--up)}.pill.dn{background:rgba(248,81,73,.16);color:#ff7b72}
.pill.flat{background:var(--hair);color:var(--mute)}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;border-radius:11px;border:0;background:var(--acc);color:var(--ink);font-weight:700;text-decoration:none}
.btn:disabled{opacity:.6}.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--fg);font-weight:600}
.note{color:var(--mute);font-size:.86rem}
.empty{color:var(--mute);padding:28px 4px}
footer{color:var(--mute);font-size:.82rem;margin-top:36px}

/* hub */
.tools{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:26px 0 22px}
.search{flex:1 1 240px;max-width:380px;height:44px;border-radius:11px;border:1px solid var(--hair);background:var(--card);color:var(--fg);font:inherit;padding:0 14px}
.search::placeholder{color:var(--mute)}
.seg{display:inline-flex;background:var(--card);border:1px solid var(--hair);border-radius:11px;padding:3px;max-width:100%;overflow-x:auto}
.seg button{min-height:38px;padding:0 14px;border:0;border-radius:8px;background:transparent;color:var(--mute);font-weight:600;font-size:.92rem;white-space:nowrap}
.seg button[aria-pressed=true],.seg button[aria-selected=true]{background:var(--raise);color:var(--fg);box-shadow:inset 0 0 0 1px var(--line)}
.hubcols{display:grid;grid-template-columns:minmax(0,1fr);gap:28px}
.group{margin-bottom:26px}
.rows{border-top:1px solid var(--hair)}
.row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;gap:16px;padding:14px 6px;min-height:76px;border-bottom:1px solid var(--hair);color:inherit;text-decoration:none;border-radius:0}
.row:hover,.row.sel{background:linear-gradient(90deg,rgba(88,166,255,.07),transparent 70%)}
.row h3{font-size:1.08rem;font-weight:700;letter-spacing:-.01em}
.row p{color:var(--mute);font-size:.9rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row svg{display:block}
.row .rt{text-align:right;min-width:92px}
.row .val{font-weight:700;font-size:1.08rem;display:block}.row .val small{font-weight:500;color:var(--mute);font-size:.8rem;margin-left:4px}
.row .rt .pill{margin-top:4px}
.panel{display:none}
.kv{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--hair);font-size:.92rem}
.kv:last-child{border-bottom:0}.kv span{color:var(--mute)}.kv b{font-weight:600;white-space:nowrap}
.rank{display:grid;grid-template-columns:minmax(0,1fr) 72px auto;gap:10px;align-items:center;padding:8px 0;font-size:.9rem}
.rank .tr{height:6px;border-radius:3px;background:var(--hair);overflow:hidden}.rank .tr i{display:block;height:100%;background:#484f58;border-radius:3px}
.rank.me{font-weight:700}.rank.me .tr i{background:var(--acc)}
.rank b{font-weight:600;min-width:58px;text-align:right}

/* model page */
.mhead{margin-bottom:22px}
.cols{display:grid;grid-template-columns:minmax(0,1fr);gap:22px}
.inputs{padding:6px 18px 0}
.grp{padding:14px 0;border-bottom:1px solid var(--hair)}.grp:last-of-type{border-bottom:0}
.grp>h2{display:flex;align-items:center;gap:8px;font-size:.86rem;font-weight:700;color:var(--mute);margin-bottom:6px}
.grp>h2 i{width:8px;height:8px;border-radius:50%;background:var(--acc)}.grp.away>h2 i{background:var(--down)}.grp.shared>h2 i{background:var(--mute)}
.f{padding:8px 0}
.fh{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:44px}
.fh label,.f>label{font-size:.95rem;font-weight:600;line-height:1.25}.fh label small{color:var(--mute);font-weight:400;margin-left:4px}
.num{width:76px;height:42px;flex:none;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:var(--r-sm);padding:0 6px;font:inherit;font-weight:700;text-align:center}
.num:focus{outline:2px solid var(--acc);outline-offset:0}
.f p{color:var(--mute);font-size:.8rem;line-height:1.35;margin-top:2px}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:36px;background:transparent;margin:0;touch-action:pan-y;--c:var(--acc);--p:50%}
.away input[type=range]{--c:var(--down)}
input[type=range]::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:linear-gradient(90deg,var(--c) var(--p),var(--line) var(--p))}
input[type=range]::-moz-range-track{height:6px;border-radius:3px;background:var(--line)}
input[type=range]::-moz-range-progress{height:6px;border-radius:3px;background:var(--c)}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:28px;height:28px;border-radius:50%;background:var(--c);border:4px solid var(--card);box-shadow:0 0 0 1px var(--line);margin-top:-11px}
input[type=range]::-moz-range-thumb{width:22px;height:22px;border-radius:50%;background:var(--c);border:4px solid var(--card);box-shadow:0 0 0 1px var(--line)}
.choice{display:flex;gap:4px;background:var(--bg);border:1px solid var(--line);border-radius:11px;padding:3px;margin-top:8px}
.choice button{flex:1;min-height:40px;border:0;border-radius:8px;background:transparent;color:var(--mute);font-weight:600}
.choice button.on{background:var(--acc);color:var(--ink)}
.actions{position:fixed;left:0;right:0;bottom:0;z-index:15;display:flex;align-items:center;gap:12px;padding:10px var(--pad) calc(10px + env(safe-area-inset-bottom));
background:rgba(22,27,34,.9);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-top:1px solid var(--line)}
.actions .mini{flex:1;min-width:0;background:none;border:0;padding:0;text-align:left;min-height:46px}
.actions .mini span{display:block;color:var(--mute);font-size:.76rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.actions .mini b{font-size:1.25rem;font-weight:800;font-variant-numeric:tabular-nums}
#dyno{min-width:118px;font-size:1.05rem}
#reset{padding:0 14px}
body.has-actions .wrap{padding-bottom:120px}
#out{scroll-margin-top:68px;min-width:0}.tabs{margin-bottom:16px}
.pane[hidden]{display:none}
.hero{padding:20px}
.hero .lab{color:var(--mute);font-size:.9rem;font-weight:600}
.big{font-size:clamp(3rem,13vw,4.4rem);font-weight:800;line-height:1;letter-spacing:-.03em;margin:6px 0 2px}
.big small{font-size:1rem;font-weight:500;color:var(--mute);margin-left:8px;letter-spacing:0}
.stale .hero{opacity:.55}.stalemsg{display:none;margin-bottom:12px;padding:10px 14px;border:1px solid var(--line);border-radius:11px;color:var(--mute);font-size:.9rem;background:var(--card)}
.stale .stalemsg{display:block}
.duo{display:flex;justify-content:space-between;align-items:flex-end;gap:12px}.duo .r{text-align:right}
.duo span{display:flex;align-items:center;gap:7px;color:var(--mute);font-size:.9rem;font-weight:600}.duo .r span{justify-content:flex-end}
.duo span i{width:8px;height:8px;border-radius:50%;background:var(--acc)}.duo .r span i{background:var(--down)}
.split{position:relative;height:14px;border-radius:7px;background:var(--down);margin:16px 0 10px}
.split>i{display:block;height:100%;border-radius:7px 0 0 7px;background:var(--acc)}
.split .band{position:absolute;top:-5px;bottom:-5px;border-left:2px solid var(--fg);border-right:2px solid var(--fg);background:rgba(230,237,243,.18);border-radius:2px}
.rng{position:relative;height:38px;margin:20px 0 6px}
.rng .trk{position:absolute;left:0;right:0;top:15px;height:8px;border-radius:4px;background:var(--hair)}
.rng .b95{position:absolute;top:11px;height:16px;border-radius:8px;background:rgba(88,166,255,.25)}
.rng .b80{position:absolute;top:8px;height:22px;border-radius:11px;background:rgba(88,166,255,.6)}
.rng .pt{position:absolute;top:2px;width:4px;height:34px;margin-left:-2px;border-radius:2px;background:#fff}
.rng .tick{position:absolute;top:0;height:38px;border-left:2px dashed var(--mute)}.rng .tick.ln{border-color:var(--warn)}
.ends{display:flex;justify-content:space-between;color:var(--mute);font-size:.8rem;font-variant-numeric:tabular-nums}
.legend{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin-top:14px;font-size:.95rem;font-weight:600;font-variant-numeric:tabular-nums}
.legend span{color:var(--mute);display:block;font-size:.8rem;font-weight:400}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.lean{margin-top:16px;padding:12px 14px;border-radius:11px;background:var(--raise);border:1px solid var(--line);font-size:.95rem}
.below{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;margin-top:16px}
.blk{padding:18px 20px}.blk h3{font-size:.86rem;color:var(--mute);font-weight:700;margin-bottom:8px}
.blk>p{max-width:64ch}
.drv{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(56px,1fr) auto;gap:12px;align-items:center;padding:10px 0;border-top:1px solid var(--hair);font-size:.93rem;font-weight:600}
.drv .nm small{color:var(--mute);display:block;font-size:.8rem;font-weight:400}
.drv .tr{position:relative;height:8px;background:var(--hair);border-radius:4px}
.drv .tr:before{content:"";position:absolute;left:50%;top:-4px;bottom:-4px;border-left:1px solid var(--mute)}
.drv .tr i{position:absolute;top:0;height:8px;border-radius:4px}
.warnbox{border:1px solid var(--warn);background:rgba(210,153,34,.1);border-radius:11px;padding:12px 14px;margin-top:16px;font-size:.9rem}
.warnbox ul{margin:4px 0 0;padding-left:18px}
.fig{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;padding:18px 0;border-top:1px solid var(--hair)}
.fig:first-child{border-top:0;padding-top:4px}
.fig img{display:block;width:100%;height:auto;border-radius:11px;border:1px solid var(--hair);background:var(--card)}
.fig h3{font-size:1.05rem;font-weight:700;margin-bottom:6px}.fig p{color:var(--fg);font-size:.93rem;max-width:58ch}
.fig .tool{display:inline-block;margin-top:10px;color:var(--mute);font-size:.8rem;border:1px solid var(--line);border-radius:6px;padding:1px 7px}
.about h3{font-size:1.05rem;font-weight:700;color:var(--fg);margin:26px 0 8px}.about h3:first-child{margin-top:0}
.about ul{margin:0;padding-left:20px}.about li{margin:0 0 8px;font-size:.95rem;max-width:68ch}
.about p{max-width:68ch}
.tw{overflow-x:auto;margin:8px 0}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:right;padding:9px 8px;border-bottom:1px solid var(--hair);white-space:nowrap}
th:first-child,td:first-child{text-align:left;white-space:normal;padding-left:0}th{color:var(--mute);font-weight:600;font-size:.8rem}
tr.me td{font-weight:700;color:var(--fg)}tr.me td:first-child{box-shadow:inset 3px 0 0 var(--acc);padding-left:10px}
.roc{display:block;width:100%;max-width:280px;margin:8px 0}
.split .cut{position:absolute;top:-7px;bottom:-7px;width:0;border-left:3px solid var(--fg);margin-left:-1.5px;border-radius:2px}
.callbox{margin-top:18px;padding-top:16px;border-top:1px solid var(--hair)}
.callbox .fh label{font-size:.95rem;font-weight:600}
.call{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:4px 0 8px;font-size:1.05rem;font-weight:700}
.call .pill{font-size:.95rem;min-width:0;padding:4px 12px}
.pill.ov{background:rgba(88,166,255,.16);color:var(--acc)}.pill.un{background:rgba(240,136,62,.16);color:var(--down)}
.trip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px}
.trip div{background:var(--raise);border:1px solid var(--hair);border-radius:11px;padding:10px 12px}
.trip b{display:block;font-size:1.25rem;font-weight:800;font-variant-numeric:tabular-nums}.trip span{color:var(--mute);font-size:.78rem;line-height:1.3;display:block}
.tname{font-size:clamp(1.9rem,8vw,2.8rem);font-weight:800;line-height:1.08;letter-spacing:-.025em;margin:6px 0 4px}
.ctype{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(48px,1fr) auto;gap:12px;align-items:center;padding:11px 0;border-top:1px solid var(--hair);font-size:.93rem;font-weight:600}
.ctype small{color:var(--mute);display:block;font-size:.8rem;font-weight:400}
.ctype .tr{height:8px;background:var(--hair);border-radius:4px;overflow:hidden}.ctype .tr i{display:block;height:100%;border-radius:4px;background:#484f58}
.ctype.me .tr i{background:var(--acc)}.ctype.me .nm{color:var(--fg)}.ctype b{font-variant-numeric:tabular-nums;font-weight:600;color:var(--mute);min-width:44px;text-align:right}
.grp.line>h2 i{background:var(--fg)}.line input[type=range]{--c:var(--fg)}.grp.line .num{border-color:var(--mute)}
.fair{margin-top:12px;padding:12px 14px;border-radius:11px;background:var(--raise);border:1px solid var(--line);font-size:.95rem}.fair b{font-variant-numeric:tabular-nums}
.grp.set>h2 i{background:var(--warn);border-radius:2px}.set input[type=range]{--c:var(--warn)}

/* sideline: Stardew-inspired pixel vignettes for the current league leaders */
.sideline{display:flex;flex-wrap:wrap;gap:12px 18px;margin-top:18px;align-items:flex-start}
.sideline[hidden]{display:none}
.sl-g{min-width:0;flex:none}
.sl-h{font-size:.78rem;font-weight:700;color:var(--mute);margin:0 0 6px 2px}
.sl-row{display:flex;gap:8px;align-items:flex-start}
.sl-p{position:relative;margin:0;width:90px;text-align:center}
.sl-scene{display:block;padding:0;margin:0 auto 5px;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;line-height:0;box-shadow:0 2px 6px rgba(0,0,0,.32);transition:transform .12s ease,border-color .12s ease}
.sl-scene:hover{transform:translateY(-1px);border-color:var(--acc)}
.px{display:block;width:88px;height:64px;image-rendering:pixelated}
.sl-p figcaption{display:flex;flex-direction:column;line-height:1.2}
.sl-p b{font-size:.94rem;font-weight:800;font-variant-numeric:tabular-nums}.sl-p span{font-size:.72rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sl-p small{font-size:.68rem;color:var(--mute)}
.sl-note{flex-basis:100%;font-size:.72rem;color:var(--mute);margin:-4px 2px 0}
@keyframes px-bob{0%,49.9%{transform:translateY(0)}50%,100%{transform:translateY(1px)}}
@keyframes px-toss{0%,52%,100%{transform:translateY(0)}58%{transform:translateY(-2px)}66%{transform:translateY(-4px)}76%{transform:translateY(-5px)}86%{transform:translateY(-4px)}93%{transform:translateY(-2px)}}
@keyframes px-tap{0%,78%,88%,100%{transform:translateY(0)}83%,93%{transform:translateY(-1px)}}
@keyframes px-steam{0%,100%{transform:translateY(0);opacity:.85}50%{transform:translateY(-2px);opacity:.35}}
@keyframes px-glow{0%,100%{opacity:1}50%{opacity:.82}}
.px-up{animation:px-bob 1.5s steps(1) infinite}.px-toss{animation:px-toss 2.8s steps(1) infinite}.px-tap{animation:px-tap 3.2s steps(1) infinite}.px-steam{animation:px-steam 2.6s steps(2) infinite}.px-glow{animation:px-glow 3.4s steps(2) infinite}
@media(prefers-reduced-motion:reduce){.px-up,.px-toss,.px-tap,.px-steam,.px-glow{animation:none}}
@media(max-width:979px){.sideline{flex-wrap:nowrap;overflow-x:auto;margin-right:calc(-1*var(--pad));padding-right:var(--pad)}.sl-note{display:none}}

/* ncr */
textarea{width:100%;min-height:120px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:var(--r);padding:14px;font:inherit;resize:vertical}
.ex{display:block;width:100%;text-align:left;background:none;border:0;border-bottom:1px solid var(--hair);padding:12px 4px;min-height:46px;color:var(--fg)}
.ex:hover{background:linear-gradient(90deg,rgba(88,166,255,.07),transparent 70%)}

@media(min-width:700px){
  .fig{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:24px;align-items:center}
  .row{padding:14px 10px}
}
@media(max-width:519px){.row .spark{display:none}.row{grid-template-columns:minmax(0,1fr) auto}}
@media(min-width:980px){
  :root{--pad:32px}
  .hubcols{grid-template-columns:minmax(0,1fr) 400px;gap:36px;align-items:start}
  .panel{display:block;position:sticky;top:76px;padding:22px}
  .panel h2{font-size:1.35rem;font-weight:800;letter-spacing:-.015em}
  .panel .sub{color:var(--mute);font-size:.93rem;margin:6px 0 16px}
  .panel .ph{color:var(--mute);font-size:.82rem;font-weight:700;margin:20px 0 4px}
  .panel .big{font-size:3rem}
  .panel .btn{width:100%;margin-top:20px}
  .mhead{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px 40px;align-items:end}.mhead .sideline{margin-top:0;justify-content:flex-end;max-width:640px}.mhead .sl-note{text-align:right}
  .cols{grid-template-columns:380px minmax(0,1fr);gap:28px;align-items:start}
  .inputs{position:sticky;top:76px;max-height:calc(100vh - 96px);overflow:auto;padding:6px 20px 0}
  .actions{position:sticky;bottom:0;left:auto;right:auto;margin:0 -20px;padding:14px 20px;background:var(--card);-webkit-backdrop-filter:none;backdrop-filter:none;border-top:1px solid var(--hair);border-radius:0 0 var(--r) var(--r)}
  .actions .mini{display:none}#dyno{flex:1}
  body.has-actions .wrap{padding-bottom:72px}
  .hero{padding:26px 28px}
}
@media(min-width:1180px){.below{grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);align-items:start}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0d1117">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230d1117'/%3E%3Crect x='9' y='9' width='14' height='14' rx='4' fill='%2358a6ff'/%3E%3C/svg%3E">
<title>__TITLE__</title><style>""" + CSS + """</style></head><body>"""

HUB = HEAD.replace("__TITLE__", "ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a></header>
<div class="wrap">
<h1 class="title">Models<span id="count">Loading</span></h1>
<p class="lede">Set the inputs, press Dyno, and see what each model predicts and why.</p>
<div class="sideline" id="sideline" hidden></div>
<div class="tools"><input class="search" id="q" type="search" placeholder="Search models" aria-label="Search models"><div class="seg" id="cats" role="group" aria-label="Category"></div></div>
<div class="hubcols"><div id="list"></div><aside class="panel card" id="panel" aria-live="polite"></aside></div>
<footer>Model numbers are test results on games each model never saw.</footer>
</div>
<script>__FIGJS__</script>
<script>
const $=id=>document.getElementById(id);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
Sideline.mount($('sideline'),'hub');
const NS='http://www.w3.org/2000/svg';
const svg=(n,at)=>{const e=document.createElementNS(NS,n);Object.keys(at).forEach(k=>e.setAttribute(k,at[k]));return e};
const n1=v=>(Math.round(v*10)/10).toFixed(1), sg=v=>(v>0?'+':v<0?'−':'')+n1(Math.abs(v));
let models=[],metas={},preds={},cat='All',sel=null;
const wide=()=>matchMedia('(min-width:980px)').matches;

/* headline test metric for a model, straight from its card */
function stat(meta){
  if(meta.type==='kmeans'){const cs=meta.card.clusters;
    return {value:String(cs.length),unit:'game types',pill:'Unsupervised',rows:cs.map(c=>({name:c.name,v:c.share,show:Math.round(c.share*100)+'%'})),flat:true,
      caption:'Share of past games in each type'}}
  const a=meta.card.accuracy.filter(x=>x.accuracy!=null||x.mae!=null),me=a[0],rest=a.slice(1);
  if(meta.type!=='linear_regression'){const best=Math.max(...rest.map(x=>x.accuracy));
    return {value:Math.round(me.accuracy*100)+'%',unit:'accuracy',diff:(me.accuracy-best)*100,good:me.accuracy>best,suffix:' pts',
      rows:a.map(x=>({name:x.name,v:x.accuracy,show:Math.round(x.accuracy*100)+'%'})),caption:'Share of test games picked right'}}
  const best=Math.min(...rest.map(x=>x.mae));
  return {value:n1(me.mae),unit:'pts avg miss',diff:me.mae-best,good:me.mae<best,suffix:' pts',
    rows:a.map(x=>({name:x.name,v:x.mae,show:n1(x.mae)+' pts'})),caption:'Average miss on test games (lower is better)'};
}
function spark(st){
  const h=8*st.rows.length-3,s=svg('svg',{viewBox:'0 0 64 '+h,width:64,height:h,'class':'spark','aria-hidden':'true'}),mx=Math.max(...st.rows.map(r=>r.v));
  st.rows.forEach((r,i)=>s.appendChild(svg('rect',{x:0,y:i*8,width:Math.max(3,r.v/mx*64),height:5,rx:2.5,fill:(i&&!st.flat)?'#484f58':'#58a6ff'})));
  return s;
}
function row(m){
  const a=el('a','row'+(sel===m.slug?' sel':''));a.href=m.url;a.dataset.slug=m.slug;
  const l=el('div');l.appendChild(el('h3',null,m.name));l.appendChild(el('p',null,m.summary));a.appendChild(l);
  const meta=metas[m.slug],rt=el('div','rt');
  if(meta){const st=stat(meta);a.appendChild(spark(st));
    const v=el('span','val',st.value);v.appendChild(el('small',null,st.unit));rt.appendChild(v);
    const p=st.pill?el('span','pill flat',st.pill):el('span','pill '+(Math.abs(st.diff)<0.05?'flat':st.good?'up':'dn'),sg(st.diff)+st.suffix);if(!st.pill)p.title='Compared with the best other method';rt.appendChild(p);
  }else{a.appendChild(el('span','spark'));rt.appendChild(el('span','pill flat','Demo'))}
  a.appendChild(rt);
  a.addEventListener('mouseenter',()=>{if(wide())pick(m.slug)});a.addEventListener('focus',()=>{if(wide())pick(m.slug)});
  return a;
}
function draw(){
  const q=$('q').value.trim().toLowerCase(),list=$('list'),cats=[...new Set(models.map(m=>m.category))];
  $('cats').replaceChildren(...['All',...cats].map(c=>{const b=el('button',null,c);b.type='button';b.setAttribute('aria-pressed',c===cat);b.onclick=()=>{cat=c;draw()};return b}));
  const show=models.filter(m=>(cat==='All'||m.category===cat)&&(!q||(m.name+' '+m.summary+' '+m.category).toLowerCase().includes(q)));
  list.replaceChildren();
  if(!show.length){const e=el('p','empty','No models match that search.');const b=el('button','btn ghost','Clear search');b.onclick=()=>{$('q').value='';cat='All';draw()};
    list.appendChild(e);list.appendChild(b);return}
  cats.forEach(c=>{const ms=show.filter(m=>m.category===c);if(!ms.length)return;
    const g=el('section','group'),h=el('div','sech');h.appendChild(el('span',null,c));h.appendChild(el('span',null,ms.length+(ms.length===1?' model':' models')));
    const r=el('div','rows');ms.forEach(m=>r.appendChild(row(m)));g.appendChild(h);g.appendChild(r);list.appendChild(g)});
}
function pick(slug){
  if(sel===slug)return;sel=slug;
  document.querySelectorAll('.row').forEach(r=>r.classList.toggle('sel',r.dataset.slug===slug));
  panel();
}
function panel(){
  const p=$('panel'),m=models.find(x=>x.slug===sel);if(!m){p.replaceChildren();return}
  const meta=metas[m.slug];p.replaceChildren();
  p.appendChild(el('p','eyebrow',m.category));p.appendChild(el('h2',null,m.name));p.appendChild(el('p','sub',m.summary));
  if(meta){
    p.appendChild(el('p','ph','With typical inputs'));const box=el('div');p.appendChild(box);preview(m.slug,meta,box);
    const st=stat(meta);p.appendChild(el('p','ph',st.caption));const mx=Math.max(...st.rows.map(r=>r.v));
    st.rows.forEach((r,i)=>{const d=el('div','rank'+((i&&!st.flat)?'':' me'));d.appendChild(el('span',null,r.name));const t=el('div','tr'),b=el('i');b.style.width=(r.v/mx*100)+'%';t.appendChild(b);d.appendChild(t);d.appendChild(el('b',null,r.show));p.appendChild(d)});
    p.appendChild(el('p','ph','Details'));
    const kv=(k,v)=>{const d=el('div','kv');d.appendChild(el('span',null,k));d.appendChild(el('b',null,v));p.appendChild(d)};
    kv('Inputs you set',meta.features.length);kv('Trained on',meta.card.n_games.toLocaleString()+' games');kv('Seasons',meta.card.seasons[0]+' to '+meta.card.seasons[1]);kv('Last trained',meta.card.trained_on);
  }
  const b=el('a','btn','Open model');b.href=m.url;p.appendChild(b);
}
function preview(slug,meta,box){
  const paint=r=>{if(!box.isConnected)return;box.replaceChildren();
    if(r.kind==='cluster'){box.appendChild(el('div','tname',r.cluster.name));
      box.appendChild(el('p','note','Games of this type average '+n1(r.cluster.profile.final_total)+' final points; the home team wins '+Math.round(r.cluster.profile.home_win*100)+'%.'));return}
    if(r.kind==='probability'){const pc=Math.round(r.probability*100),duo=el('div','duo'),l=el('div'),rt=el('div','r');
      const a=el('span');a.appendChild(el('i'));a.appendChild(document.createTextNode(r.labels.positive));l.appendChild(a);l.appendChild(el('div','big',pc+'%'));
      const c=el('span');c.appendChild(document.createTextNode(r.labels.negative));c.appendChild(el('i'));rt.appendChild(c);rt.appendChild(el('div','big',(100-pc)+'%'));
      duo.appendChild(l);duo.appendChild(rt);box.appendChild(duo);const s=el('div','split'),i=el('i');i.style.width=(r.probability*100)+'%';s.appendChild(i);box.appendChild(s);
    }else{const u=meta.target.unit||'',big=el('div','big',n1(r.prediction));big.appendChild(el('small',null,u));box.appendChild(big);
      box.appendChild(el('p','note','Likely range '+Math.round(r.intervals['80'].low)+' to '+Math.round(r.intervals['80'].high)+' '+u))}};
  if(preds[slug])return paint(preds[slug]);
  box.appendChild(el('p','note','Running the model'));
  const inputs={};meta.features.forEach(f=>inputs[f.name]=f.default);
  fetch('/api/models/'+slug+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inputs})})
    .then(r=>r.ok?r.json():Promise.reject()).then(r=>{preds[slug]=r;if(sel===slug)paint(r)}).catch(()=>{if(box.isConnected)box.replaceChildren(el('p','note','Preview unavailable right now.'))});
}
$('q').addEventListener('input',draw);
fetch('/api/models').then(r=>r.json()).then(d=>{
  models=d.models;const cats=new Set(models.map(m=>m.category)).size;
  $('count').textContent=models.length+' live in '+cats+(cats===1?' category':' categories');
  draw();
  return Promise.all(models.filter(m=>m.url.indexOf('/m/')===0).map(m=>fetch('/api/models/'+m.slug).then(r=>r.ok?r.json():null).then(j=>{if(j)metas[m.slug]=j}).catch(()=>{})));
}).then(()=>{draw();if(models.length){sel=null;pick(models[0].slug)}})
.catch(()=>{$('count').textContent='Unavailable';$('list').replaceChildren(el('p','empty','Could not load the models. Refresh to try again.'))});
</script></body></html>"""

MODEL = HEAD.replace("__TITLE__", "__NAME__ · ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a><span class="crumb" id="crumb"></span></header>
<div class="wrap">
<div class="mhead"><div><p class="eyebrow" id="cat"></p><h1 class="title" id="name">__NAME__</h1><p class="lede" id="summary"></p></div>
<div class="sideline" id="sideline" hidden></div></div>
<div class="cols">
  <section class="inputs card" id="inputs" aria-label="Inputs">
    <div id="groups"></div>
    <div class="actions"><button class="mini" id="mini" type="button" aria-label="Jump to the prediction"><span id="miniLab">Prediction</span><b id="miniVal">–</b></button>
      <button class="btn ghost" id="reset" type="button">Reset</button><button class="btn" id="dyno" type="button">Dyno</button></div>
  </section>
  <div id="out">
    <div class="seg tabs" role="tablist" aria-label="Model sections">
      <button role="tab" id="t-pred" aria-selected="true" aria-controls="p-pred" type="button">Prediction</button>
      <button role="tab" id="t-diag" aria-selected="false" aria-controls="p-diag" type="button">Diagnostics</button>
      <button role="tab" id="t-about" aria-selected="false" aria-controls="p-about" type="button">About</button>
    </div>
    <div class="pane" id="p-pred" role="tabpanel" aria-labelledby="t-pred"><p class="stalemsg">Inputs changed. Press Dyno to update the prediction.</p><div id="result"><p class="empty">Running the model with typical inputs.</p></div></div>
    <div class="pane" id="p-diag" role="tabpanel" aria-labelledby="t-diag" hidden><p class="note" id="diagLede" style="margin-bottom:10px"></p><div id="plotList"></div></div>
    <div class="pane about card blk" id="p-about" role="tabpanel" aria-labelledby="t-about" hidden></div>
    <footer id="foot"></footer>
  </div>
</div>
</div>
<script>__FIGJS__</script>
<script>
const SLUG="__SLUG__";
const $=id=>document.getElementById(id);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const n1=v=>(Math.round(v*10)/10).toString(), n0=v=>Math.round(v).toString();
const sg=v=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(1);
let meta,vals={},pvals={},ctl={},lineInput,ran=false,last=null,cut=null;
document.body.classList.add('has-actions');
Sideline.mount($('sideline'),SLUG);

function tab(id){['pred','diag','about'].forEach(k=>{$('t-'+k).setAttribute('aria-selected',k===id);$('p-'+k).hidden=k!==id})}
['pred','diag','about'].forEach(k=>$('t-'+k).onclick=()=>tab(k));
function stale(){if(ran)$('p-pred').classList.add('stale')}

function field(f,store){store=store||vals;
  if(f.choices){const w=el('div','f'),seg=el('div','choice'),btn={};w.appendChild(el('label',null,f.label));
    const set=(v,user)=>{store[f.name]=v;Object.keys(btn).forEach(k=>{btn[k].className=(+k===v?'on':'');btn[k].setAttribute('aria-pressed',+k===v)});if(user)stale()};
    Object.keys(f.choices).forEach(k=>{const b=el('button',null,f.choices[k]);b.type='button';b.onclick=()=>set(+k,true);btn[k]=b;seg.appendChild(b)});
    ctl[f.name]=set;set(f.default);w.appendChild(seg);w.appendChild(el('p',null,f.description));return w}
  const w=el('div','f'),h=el('div','fh'),lab=el('label',null,f.label);
  if(f.unit)lab.appendChild(el('small',null,f.unit));
  const num=el('input','num');num.type='number';num.inputMode='decimal';num.step=f.step;num.min=f.hard_min;num.max=f.hard_max;
  const rng=el('input');rng.type='range';rng.min=f.min;rng.max=f.max;rng.step=f.step;
  lab.htmlFor=num.id='n_'+f.name;rng.setAttribute('aria-label',f.label);
  const set=(v,from)=>{v=Math.min(f.hard_max,Math.max(f.hard_min,v));store[f.name]=v;if(from!=='num')num.value=v;if(from!=='rng')rng.value=v;
    rng.style.setProperty('--p',Math.min(100,Math.max(0,(v-f.min)/(f.max-f.min)*100))+'%');if(from)stale()};
  rng.oninput=()=>set(parseFloat(rng.value),'rng');
  num.oninput=()=>{const v=parseFloat(num.value);if(!isNaN(v))set(v,'num')};
  num.onblur=()=>{num.value=store[f.name]};
  ctl[f.name]=set;set(f.default);
  h.appendChild(lab);h.appendChild(num);w.appendChild(h);w.appendChild(rng);w.appendChild(el('p',null,f.description));
  return w;
}
function build(){
  $('cat').textContent=meta.category;$('crumb').textContent=meta.category;$('name').textContent=meta.name;$('summary').textContent=meta.summary;
  const box=$('groups'),sides=[['home','Home'],['away','Away']].filter(s=>meta.features.some(f=>f.side===s[0]));
  const grp=(cls,title,fs)=>{const g=el('div','grp '+cls),h=el('h2');h.appendChild(el('i'));h.appendChild(document.createTextNode(title));g.appendChild(h);fs.forEach(f=>g.appendChild(field(f)));box.appendChild(g);return g};
  const ln=meta.features.filter(f=>f.side==='line');if(ln.length)grp('line','Your total',ln);
  sides.forEach(([k,title])=>grp(k,title,meta.features.filter(f=>f.side===k)));
  const sh=meta.features.filter(f=>f.side==='shared');
  if(sh.length)grp('shared',sides.length?'Game context':'Inputs',sh);
  if(meta.compare_line){const g=grp('shared','Compare',[]),w=el('div','f'),h=el('div','fh'),lab=el('label',null,meta.compare_line.label);
    lineInput=el('input','num');lineInput.type='number';lineInput.inputMode='decimal';lineInput.step=meta.compare_line.step;lineInput.placeholder='–';lineInput.id='line';lab.htmlFor='line';
    lineInput.oninput=stale;h.appendChild(lab);h.appendChild(lineInput);w.appendChild(h);g.appendChild(w)}
  if((meta.controls||[]).length){const g=grp('shared set','Model settings',[]);
    meta.controls.forEach(c=>g.appendChild(field({name:c.name,label:c.label,unit:'',step:c.step,min:c.min,max:c.max,hard_min:c.min,hard_max:c.max,default:c.default,description:c.description},pvals)))}
  if(meta.target.cutoff)cut=meta.target.cutoff.default;
  $('miniLab').textContent=meta.target.label;
  plots();about();$('foot').textContent=meta.card.disclaimer||'';
}
function plots(){
  const box=$('plotList'),ps=meta.plots||[];
  if(!ps.length){$('diagLede').textContent='';box.appendChild(el('p','empty','No diagnostic plots have been published for this model yet.'));return}
  $('diagLede').textContent='The standard checks for this kind of model, drawn from its real test games, each with a short reading guide.';
  ps.forEach(p=>{const f=el('figure','fig');f.style.margin='0';const im=el('img');im.src=p.url;im.loading='lazy';im.alt=p.title+'. '+p.text;f.appendChild(im);
    const c=el('figcaption');c.appendChild(el('h3',null,p.title));c.appendChild(el('p',null,p.text));c.appendChild(el('span','tool','Made with '+p.tool));f.appendChild(c);box.appendChild(f)});
}
function about(){
  const c=meta.card,b=$('p-about');
  b.appendChild(el('h3',null,'What the model learned'));
  const ul=el('ul');c.findings.forEach(t=>ul.appendChild(el('li',null,t)));b.appendChild(ul);
  const table=(head,rows,first)=>{const t=el('table'),hr=el('tr');head.forEach(x=>hr.appendChild(el('th',null,x)));t.appendChild(hr);
    rows.forEach((cells,i)=>{const r=el('tr',first&&!i?'me':'');cells.forEach(x=>r.appendChild(el('td',null,x)));t.appendChild(r)});const w=el('div','tw');w.appendChild(t);return w};
  const sections=()=>(c.sections||[]).forEach(sec=>{b.appendChild(el('h3',null,sec.title));(sec.paragraphs||[]).forEach(t=>{const p=el('p',null,t);p.style.marginBottom='8px';b.appendChild(p)});
    if(sec.table)b.appendChild(table(sec.table.head,sec.table.rows,!!sec.note));if(sec.note)b.appendChild(el('p','note',sec.note))});
  if(!c.accuracy)sections();
  if(c.accuracy){
  b.appendChild(el('h3',null,'How accurate is it?'));
  b.appendChild(el('p','note','Tested on the '+c.holdout_label+'.'));
  const cols=c.accuracy_columns||[['mae','Average miss','pts'],['rmse','RMSE','num1'],['r2','R²','num']];
  const show=(v,k)=>v==null?'–':k==='pct'?Math.round(v*100)+'%':k==='pts'?v.toFixed(1)+' pts':k==='pct1'?(v*100).toFixed(1)+'%':k==='num1'?v.toFixed(1):k==='num3'?v.toFixed(3):v.toFixed(2);
  const t=el('table'),hr=el('tr');['Method',...cols.map(x=>x[1])].forEach(x=>hr.appendChild(el('th',null,x)));t.appendChild(hr);
  c.accuracy.forEach((a,i)=>{const r=el('tr',i?'':'me');r.appendChild(el('td',null,a.name));cols.forEach(x=>r.appendChild(el('td',null,show(a[x[0]],x[2]))));t.appendChild(r)});
  const tw=el('div','tw');tw.appendChild(t);b.appendChild(tw);
  b.appendChild(el('p','note',c.metric_note||'Average miss is how far off the prediction was on a typical game. RMSE is similar but punishes big misses more. R² is the share of game-to-game differences the method explains (1.00 would be perfect).'));
  sections();}
  if(c.roc&&!(meta.plots||[]).length){b.appendChild(el('h3',null,'ROC curve'));
    const NS='http://www.w3.org/2000/svg',sv=document.createElementNS(NS,'svg');sv.setAttribute('viewBox','0 0 220 220');sv.setAttribute('class','roc');
    const mk=(n,at)=>{const e=document.createElementNS(NS,n);Object.keys(at).forEach(k=>e.setAttribute(k,at[k]));sv.appendChild(e);return e};
    mk('rect',{x:30,y:10,width:180,height:180,fill:'none',stroke:'#30363d'});
    mk('line',{x1:30,y1:190,x2:210,y2:10,stroke:'#8b949e','stroke-dasharray':'4 4'});
    mk('polyline',{points:c.roc.map(p=>(30+p[0]*180)+','+(190-p[1]*180)).join(' '),fill:'none',stroke:'#58a6ff','stroke-width':3});
    mk('text',{x:120,y:212,fill:'#8b949e','font-size':11,'text-anchor':'middle'}).textContent='False alarms (away wins called home)';
    mk('text',{x:12,y:100,fill:'#8b949e','font-size':11,'text-anchor':'middle',transform:'rotate(-90 12 100)'}).textContent='Home wins caught';
    b.appendChild(sv);
    b.appendChild(el('p','note','The further the blue line bows toward the top-left corner, the better the model separates wins from losses. The dashed line is a coin flip.'))}
  if(c.calibration){b.appendChild(el('h3',null,'Can you trust the percentages?'));
    b.appendChild(el('p','note','Test games grouped by what the model said, next to what really happened. Close numbers mean the percentages are honest.'));
    const ct=el('table'),ch=el('tr');['Model said','Games','Avg predicted',c.calibration_label||'Home actually won'].forEach(x=>ch.appendChild(el('th',null,x)));ct.appendChild(ch);
    c.calibration.forEach(k=>{const r=el('tr');[k.range,k.n,Math.round(k.predicted*100)+'%',Math.round(k.actual*100)+'%'].forEach(x=>r.appendChild(el('td',null,x)));ct.appendChild(r)});
    const cw=el('div','tw');cw.appendChild(ct);b.appendChild(cw);
    if(c.confident&&c.confident.accuracy!=null&&c.confident.tossup_accuracy!=null)b.appendChild(el('p',null,'When the model was at least 80% sure (about '+Math.round(c.confident.share*100)+'% of test games), it was right '+Math.round(c.confident.accuracy*100)+'% of the time. When it was under 60% sure, it was right '+Math.round(c.confident.tossup_accuracy*100)+'% of the time.'))}
  if(c.coverage){b.appendChild(el('h3',null,'Can you trust the range?'));
    b.appendChild(el('p',null,'In the test games, the real final score landed inside the 80% range '+Math.round(c.coverage['80']*100)+'% of the time and inside the 95% range '+Math.round(c.coverage['95']*100)+'% of the time. That is what honest ranges should do.'))}
  b.appendChild(el('h3',null,'Limitations'));
  const ul2=el('ul');c.limitations.forEach(t=>ul2.appendChild(el('li',null,t)));b.appendChild(ul2);
  const tn=el('p','note',(c.model_kind||'Linear regression')+' trained on '+c.n_games.toLocaleString()+' games from the '+c.seasons[0]+' to '+c.seasons[1]+' seasons, after testing '+c.candidates_tested+' candidate inputs'+(c.sections?' and the settings shown above':'')+'. Last trained '+c.trained_on+'. Data: nflverse.');
  tn.style.marginTop='18px';b.appendChild(tn);
}
function below(box,r,note,head,pf){pf=pf||sg;
  const g=el('div','below');
  const why=el('div','card blk');why.appendChild(el('h3',null,'The short version'));why.appendChild(el('p',null,r.synopsis));
  if(r.warnings.length){const w=el('div','warnbox');w.appendChild(el('b',null,'Unusual inputs'));const ul=el('ul');r.warnings.forEach(t=>ul.appendChild(el('li',null,t)));w.appendChild(ul);why.appendChild(w)}
  g.appendChild(why);
  const d=el('div','card blk');d.appendChild(el('h3',null,head||'What moved this prediction'));const nt=el('p','note',note);nt.style.marginBottom='10px';d.appendChild(nt);
  const mx=Math.max(1,...r.drivers.map(x=>Math.abs(x.effect)));
  r.drivers.forEach(x=>{const row=el('div','drv'),nm=el('div','nm',(x.side?x.side+' ':'')+x.label.toLowerCase().replace(/^./,c=>x.side?c:c.toUpperCase()));
    nm.appendChild(el('small',null,(x.value_label||n1(x.value)+(x.unit?' '+x.unit:''))+(x.computed?' (computed)':'')+(x.typical!=null?', typical '+n1(x.typical):'')));
    const tr=el('div','tr'),i=el('i'),w=Math.abs(x.effect)/mx*50;i.style.width=w+'%';i.style.left=x.effect>=0?'50%':(50-w)+'%';
    i.style.background=x.effect>=0?'var(--up)':'var(--neg)';tr.appendChild(i);
    const tiny=Math.abs(x.effect)<0.05;row.appendChild(nm);row.appendChild(tr);row.appendChild(el('span','pill '+(tiny?'flat':x.effect>=0?'up':'dn'),tiny?'0.0':pf(x.effect)));d.appendChild(row)});
  g.appendChild(d);box.appendChild(g);
}
function renderProb(r){
  const box=$('result');box.replaceChildren();const p=r.probability,P=r.labels.positive,N=r.labels.negative,pc=Math.round(p*100),T=meta.target;
  const hero=el('div','card hero');hero.appendChild(el('p','lab',r.headline||T.headline||'Chance to win the game'));
  const duo=el('div','duo'),l=el('div'),rt=el('div','r');
  const a=el('span');a.appendChild(el('i'));a.appendChild(document.createTextNode(P));l.appendChild(a);l.appendChild(el('div','big',pc+'%'));
  const c=el('span');c.appendChild(document.createTextNode(N));c.appendChild(el('i'));rt.appendChild(c);rt.appendChild(el('div','big',(100-pc)+'%'));
  duo.appendChild(l);duo.appendChild(rt);hero.appendChild(duo);
  const sp=el('div','split'),i=el('i');i.style.width=(p*100)+'%';sp.appendChild(i);hero.appendChild(sp);
  if(r.intervals){const i95=r.intervals['95'],band=el('div','band');band.style.left=(i95.low*100)+'%';band.style.width=Math.max(0.6,(i95.high-i95.low)*100)+'%';sp.appendChild(band);
    hero.appendChild(el('p','note','The marked band is the 95% range for the true '+P.toLowerCase()+' chance in games like this: '+Math.round(i95.low*100)+'% to '+Math.round(i95.high*100)+'%.'))}
  if(r.detail)hero.appendChild(el('p','note',r.detail));
  if(r.fair_line!=null&&r.need>=0){const f=el('div','fair');f.appendChild(document.createTextNode('Break-even total for this game: '));f.appendChild(el('b',null,n1(r.fair_line)));
    f.appendChild(document.createTextNode('. That is where the model is 50/50. Your total of '+n1(r.line)+' is '+(Math.abs(r.line-r.fair_line)<0.25?'right on it.':n1(Math.abs(r.line-r.fair_line))+' '+(r.line>r.fair_line?'above':'below')+' it.')));hero.appendChild(f)}
  if(T.cutoff)cutoff(hero,sp,p,P,N);
  box.appendChild(hero);
  const subj=T.subject?'the chance of '+T.subject:'the win chance for the '+P.toLowerCase()+' team';
  if(T.cutoff)below(box,r,'Each row puts one halftime input back to its typical value, keeps your total the same, and shows how many percentage points '+subj+' moves because of what you entered instead.');
  else below(box,r,'Start from an average game ('+Math.round(r.baseline*100)+'% '+P.toLowerCase()+'). Each row shows how many percentage points that input, on its own, moves '+subj+'.');
  $('miniVal').textContent=P+' '+pc+'%';
}
/* movable cutoff: turns the percentage into a call, and shows what that cutoff did on games the model had not seen */
function cutoff(hero,sp,p,P,N){
  const C=meta.target.cutoff,tbl=meta.card.threshold_table||[],w=el('div','callbox'),h=el('div','fh'),lab=el('label',null,'Your cutoff for calling it '+P.toLowerCase());
  const num=el('input','num');num.type='number';num.inputMode='numeric';num.min=C.min*100;num.max=C.max*100;num.step=1;num.id='cutNum';lab.htmlFor='cutNum';
  const rng=el('input');rng.type='range';rng.min=C.min*100;rng.max=C.max*100;rng.step=1;rng.setAttribute('aria-label','Cutoff percent');
  const mark=el('div','cut');sp.appendChild(mark);
  const call=el('div','call'),trip=el('div','trip'),note=el('p','note');note.style.marginTop='10px';
  const pct=v=>Math.round(v*100)+'%';
  const set=(v,from)=>{v=Math.min(C.max*100,Math.max(C.min*100,Math.round(v)));cut=v/100;if(from!=='num')num.value=v;if(from!=='rng')rng.value=v;
    rng.style.setProperty('--p',((v-C.min*100)/((C.max-C.min)*100)*100)+'%');mark.style.left=v+'%';
    const over=p>=cut;call.replaceChildren(document.createTextNode('Call:'),el('span','pill '+(over?'ov':'un'),over?P:N),
      el('span','note',Math.round(p*100)+'% is '+(over?'at or above':'below')+' your '+v+'% cutoff'));
    const row=tbl.find(t=>Math.round(t.cutoff*100)===v);trip.replaceChildren();
    if(row){const cell=(big,txt)=>{const d=el('div');d.appendChild(el('b',null,big));d.appendChild(el('span',null,txt));trip.appendChild(d)};
      cell(pct(row.over_right),P.toLowerCase()+' calls that were right');cell(pct(row.under_right),N.toLowerCase()+' calls that were right');cell(pct(row.called_over),'of games called '+P.toLowerCase());
      note.textContent='At a '+v+'% cutoff the model was right on '+pct(row.accuracy)+' of games overall and caught '+pct(row.overs_caught)+' of the games that went '+P.toLowerCase()+'. Raise the cutoff and '+P.toLowerCase()+' calls get rarer but more reliable. '+(meta.card.threshold_note||'')}};
  rng.oninput=()=>set(parseFloat(rng.value),'rng');num.oninput=()=>{const v=parseFloat(num.value);if(!isNaN(v)&&v>=C.min*100&&v<=C.max*100)set(v,'num')};num.onblur=()=>{num.value=Math.round(cut*100)};
  h.appendChild(lab);h.appendChild(num);w.appendChild(h);w.appendChild(rng);w.appendChild(call);w.appendChild(trip);w.appendChild(note);hero.appendChild(w);
  set((cut??C.default)*100);
}
function renderCluster(r){
  const box=$('result');box.replaceChildren();const c=r.cluster,pr=c.profile,all=r.overall;
  const hero=el('div','card hero');hero.appendChild(el('p','lab','This halftime looks like'));
  hero.appendChild(el('div','tname',c.name));
  hero.appendChild(el('p','note','One of '+r.k+' game types. About '+Math.round(c.share*100)+'% of past games ('+pr.games.toLocaleString()+') are this type.'+(r.border?' Border case: the next type is almost as close.':'')));
  const trip=el('div','trip');const cell=(big,txt)=>{const d=el('div');d.appendChild(el('b',null,big));d.appendChild(el('span',null,txt));trip.appendChild(d)};
  cell(n1(pr.final_total),'avg final points (all games '+n1(all.final_total)+')');cell(Math.round(pr.home_win*100)+'%','home team won (all games '+Math.round(all.home_win*100)+'%)');
  cell(Math.round(pr.over*100)+'%','went over the pregame total');hero.appendChild(trip);
  const nt=el('p','note','How games of this type finished. The model never saw final scores; these were looked up after grouping.');nt.style.marginTop='10px';hero.appendChild(nt);
  box.appendChild(hero);
  const list=el('div','card blk');list.style.marginTop='16px';list.appendChild(el('h3',null,'How close you are to each type'));
  const ln=el('p','note','Distance from your inputs to the centre of each type, in standard deviations. Shorter is closer. Each row also shows that type’s average halftime score and how its games finished.');ln.style.marginBottom='10px';list.appendChild(ln);
  const mx=Math.max(...r.clusters.map(x=>x.distance));
  r.clusters.forEach((x,i)=>{const row=el('div','ctype'+(i?'':' me')),nm=el('div','nm',x.name);
    nm.appendChild(el('small',null,'Centre '+Math.round(x.centroid.home_h1_pts)+'–'+Math.round(x.centroid.away_h1_pts)+' at half, finishes '+n1(x.profile.final_total)+' pts, home wins '+Math.round(x.profile.home_win*100)+'%'));
    const tr=el('div','tr'),b=el('i');b.style.width=Math.max(4,x.distance/mx*100)+'%';tr.appendChild(b);row.appendChild(nm);row.appendChild(tr);row.appendChild(el('b',null,x.distance.toFixed(2)));list.appendChild(row)});
  box.appendChild(list);
  below(box,r,'How far each input sits from an average halftime, in standard deviations. Right of centre is above average.','What stands out about this halftime',v=>sg(v)+' SD');
  $('miniVal').textContent=c.name;
}
function render(r){
  ran=true;last=r;$('p-pred').classList.remove('stale');
  if(r.kind==='probability')return renderProb(r);
  if(r.kind==='cluster')return renderCluster(r);
  const u=meta.target.unit||'',box=$('result');box.replaceChildren();
  const hero=el('div','card hero');hero.appendChild(el('p','lab','Expected '+meta.target.label.toLowerCase()));
  const big=el('div','big',n1(r.prediction));big.appendChild(el('small',null,u));hero.appendChild(big);
  const i80=r.intervals['80'],i95=r.intervals['95'];
  let a=Math.min(i95.low,r.floor??i95.low),b=i95.high;
  if(r.compare){a=Math.min(a,r.compare.line);b=Math.max(b,r.compare.line)}
  const pad=(b-a)*0.06;a-=pad;b+=pad;const pos=v=>((v-a)/(b-a)*100)+'%',wid=(x,y)=>((y-x)/(b-a)*100)+'%';
  const g=el('div','rng');g.appendChild(el('div','trk'));
  const b95=el('div','b95');b95.style.left=pos(i95.low);b95.style.width=wid(i95.low,i95.high);g.appendChild(b95);
  const b80=el('div','b80');b80.style.left=pos(i80.low);b80.style.width=wid(i80.low,i80.high);g.appendChild(b80);
  if(r.floor!=null){const t=el('div','tick');t.style.left=pos(r.floor);g.appendChild(t)}
  if(r.compare){const t=el('div','tick ln');t.style.left=pos(r.compare.line);g.appendChild(t)}
  const pt=el('div','pt');pt.style.left=pos(r.prediction);g.appendChild(pt);hero.appendChild(g);
  const ends=el('div','ends');ends.appendChild(el('span',null,n0(a)));ends.appendChild(el('span',null,n0(b)));hero.appendChild(ends);
  const lg=el('div','legend');
  const item=(color,title,text,dashed)=>{const d=el('div'),s=el('span');const sw=el('i','sw');
    if(dashed){sw.style.width='0';sw.style.borderLeft='2px dashed '+color;sw.style.height='12px';sw.style.borderRadius='0'}else sw.style.background=color;
    s.appendChild(sw);s.appendChild(document.createTextNode(title));d.appendChild(s);d.appendChild(document.createTextNode(text));lg.appendChild(d)};
  item('rgba(88,166,255,.75)','Likely range (80%)',n0(i80.low)+' to '+n0(i80.high)+' '+u);
  item('rgba(88,166,255,.3)','Almost certain (95%)',n0(i95.low)+' to '+n0(i95.high)+' '+u);
  if(r.floor!=null)item('#8b949e',meta.floor.label.replace(/^./,c=>c.toUpperCase()),n1(r.floor)+' '+u,true);
  if(r.compare)item('#d29922','Line you entered',n1(r.compare.line)+' '+u,true);
  hero.appendChild(lg);
  if(r.compare){const c=r.compare,l=el('div','lean');
    l.textContent=Math.abs(c.gap)<1.5?'Right on the line. No real lean either way ('+Math.round(c.p_over*100)+'% chance of going over).'
      :'Model leans '+c.lean.toUpperCase()+' by '+n1(Math.abs(c.gap))+' '+u+'. About '+Math.round(c.p_over*100)+'% chance of going over.';
    hero.appendChild(l)}
  box.appendChild(hero);
  below(box,r,'Start from an average game ('+n1(r.baseline)+' '+u+'). Each row shows how many points your input adds or removes.');
  $('miniVal').textContent=n1(r.prediction)+' '+u;
}
async function run(user){
  const btn=$('dyno');btn.disabled=true;btn.textContent='Running';
  try{
    const body={inputs:vals};if(Object.keys(pvals).length)body.params=pvals;const lv=lineInput?parseFloat(lineInput.value):NaN;if(!isNaN(lv))body.line=lv;
    const r=await fetch('/api/models/'+SLUG+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const j=await r.json();if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:'check the inputs and try again');render(j);
    if(user){tab('pred');if(!matchMedia('(min-width:980px)').matches)$('out').scrollIntoView({behavior:'smooth',block:'start'})}
  }catch(e){$('result').replaceChildren(el('p','empty','The model did not run: '+e.message+'. Press Dyno to try again.'));if(user)tab('pred')}
  btn.disabled=false;btn.textContent='Dyno';
}
fetch('/api/models/'+SLUG).then(r=>r.ok?r.json():Promise.reject()).then(m=>{meta=m;build();
  $('dyno').onclick=()=>run(true);
  $('mini').onclick=()=>{tab('pred');$('out').scrollIntoView({behavior:'smooth',block:'start'})};
  $('reset').onclick=()=>{meta.features.forEach(f=>ctl[f.name](f.default));(meta.controls||[]).forEach(c=>ctl[c.name](c.default));if(meta.target.cutoff)cut=meta.target.cutoff.default;if(lineInput)lineInput.value='';run(false)};
  run(false);
}).catch(()=>{$('result').replaceChildren(el('p','empty','Could not load this model. Refresh to try again.'))});
</script></body></html>"""

NCR = HEAD.replace("__TITLE__", "NCR Classifier · ddyno") + """
<header class="top"><a class="brand" href="/"><i></i>ddyno</a><span class="crumb">Manufacturing</span></header>
<div class="wrap" style="max-width:820px">
<div class="mhead"><p class="eyebrow">Manufacturing</p><h1 class="title">NCR Classifier</h1>
<p class="lede">Paste a non-conformance description and get the likely flaw category. Demo model: TF-IDF and logistic regression trained on a small synthetic set.</p></div>
<label class="sech" for="t">Description</label>
<textarea id="t" placeholder="For example: bore diameter oversize after final grind"></textarea>
<div style="display:flex;gap:12px;margin:14px 0 26px"><button class="btn" id="go" type="button">Classify</button></div>
<div id="out"></div>
<div class="sech" style="margin-top:26px"><span>Try an example</span></div>
<div class="rows" id="ex"></div>
</div>
<script>
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const ex=["scratches on sealing surface","missing washer during final assembly","calibration sticker expired on gauge","porosity found in casting"];
const t=document.getElementById('t'),out=document.getElementById('out'),go=document.getElementById('go');
ex.forEach(s=>{const b=el('button','ex',s);b.type='button';b.onclick=()=>{t.value=s;run()};document.getElementById('ex').appendChild(b)});
async function run(){
  if(t.value.trim().length<3){out.replaceChildren(el('p','note','Enter at least a few words to classify.'));return}
  go.disabled=true;go.textContent='Classifying';
  try{
    const r=await fetch('/api/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})});
    if(!r.ok)throw new Error(r.status);
    const {predictions}=await r.json();const card=el('div','card blk');card.appendChild(el('h3',null,'Most likely categories'));
    predictions.forEach((p,i)=>{const d=el('div','rank'+(i?'':' me'));d.style.gridTemplateColumns='minmax(0,1fr) minmax(72px,1fr) auto';d.appendChild(el('span',null,p.label));
      const tr=el('div','tr'),b=el('i');b.style.width=(p.score*100)+'%';tr.appendChild(b);d.appendChild(tr);d.appendChild(el('b',null,(p.score*100).toFixed(1)+'%'));card.appendChild(d)});
    out.replaceChildren(card);
  }catch(e){out.replaceChildren(el('p','note','Could not classify that text. Try again.'))}
  go.disabled=false;go.textContent='Classify';
}
go.onclick=run;
</script></body></html>"""

HUB = HUB.replace("__FIGJS__", FIGJS)
MODEL = MODEL.replace("__FIGJS__", FIGJS)
