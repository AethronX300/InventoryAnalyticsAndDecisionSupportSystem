"""
Meridian · Inventory IQ  —  theme.
The whole look of the original app (glass cards, colours, fonts, animations) lives here as
plain strings so the project stays 100% Python files — no assets folder, no Node, no Tailwind.
"""
from urllib.parse import quote

# --------------------------------------------------------------------------- #
# icons (24x24 stroke icons, rendered as CSS masks so they inherit `color`)
# --------------------------------------------------------------------------- #
ICONS = {
    "grid": '<rect x="3.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.6"/>',
    "box": '<path d="M12 3 4 7v10l8 4 8-4V7l-8-4Z"/><path d="m4 7 8 4 8-4M12 11v10"/>',
    "receipt": '<path d="M6 3h12v18l-2-1.4L14 21l-2-1.4L10 21l-2-1.4L6 21V3Z"/><path d="M9.5 8h5M9.5 12h5"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7.5 14 3.5-4 3 2.5L18 7"/><circle cx="18" cy="7" r="1.2"/>',
    "compass": '<circle cx="12" cy="12" r="8.5"/><path d="m15.2 8.8-1.8 4.6-4.6 1.8 1.8-4.6 4.6-1.8Z"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "sliders": '<path d="M5 6h14M5 12h14M5 18h14"/><circle cx="9" cy="6" r="1.8" fill="black" stroke="none"/><circle cx="15" cy="12" r="1.8" fill="black" stroke="none"/><circle cx="8" cy="18" r="1.8" fill="black" stroke="none"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "x": '<path d="m6 6 12 12M18 6 6 18"/>',
    "chevronDown": '<path d="m6 9.5 6 6 6-6"/>',
    "chevronRight": '<path d="m9.5 6 6 6-6 6"/>',
    "arrowUp": '<path d="M12 19V5m0 0-5.5 5.5M12 5l5.5 5.5"/>',
    "arrowDown": '<path d="M12 5v14m0 0 5.5-5.5M12 19l-5.5-5.5"/>',
    "alert": '<path d="M12 3.5 2.5 20h19L12 3.5Z"/><path d="M12 10v4.5M12 17.4v.2"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "truck": '<path d="M2.5 6h11v11h-11zM13.5 10h4l3 3.5V17h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    "external": '<path d="M9 5H5v14h14v-4"/><path d="M13 4h7v7M20 4l-9 9"/>',
    "sparkle": '<path d="M12 3.5c.6 3.8 2.7 5.9 6.5 6.5-3.8.6-5.9 2.7-6.5 6.5-.6-3.8-2.7-5.9-6.5-6.5 3.8-.6 5.9-2.7 6.5-6.5Z"/><path d="M18.5 15.5c.3 1.7 1.3 2.7 3 3-1.7.3-2.7 1.3-3 3-.3-1.7-1.3-2.7-3-3 1.7-.3 2.7-1.3 3-3Z"/>',
    "pulse": '<path d="M3 12h4l2.5-6 4 12L16 12h5"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.9-3M4 13a8 8 0 0 0 14.9 3"/><path d="M20 4v4h-4M4 20v-4h4"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 7.6v.2"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "scale": '<path d="M12 4v16M4 8h16"/><path d="m7 8-3 6a3.2 3.2 0 0 0 6 0L7 8ZM17 8l-3 6a3.2 3.2 0 0 0 6 0l-3-6Z"/><path d="M8 20h8"/>',
    "leaf": '<path d="M5 19c0-8 4-13 14-14 .5 10-4 14-11 14H5Z"/><path d="M5 19c2-5 5-8 9-10"/>',
    "tag": '<path d="m3.5 12.5 8-8.5H20v8.5l-8 8.5a1.4 1.4 0 0 1-2 0l-6.5-6.5a1.4 1.4 0 0 1 0-2Z"/><circle cx="15.5" cy="8.5" r="1.2"/>',
    "database": '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.8"/><path d="M4.5 5.5v13c0 1.6 3.4 2.8 7.5 2.8s7.5-1.2 7.5-2.8v-13"/><path d="M4.5 12c0 1.6 3.4 2.8 7.5 2.8s7.5-1.2 7.5-2.8"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
}


def _icon_css() -> str:
    out = []
    for name, body in ICONS.items():
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
               "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>" + body.replace('"', "'") + "</svg>")
        url = 'url("data:image/svg+xml,' + quote(svg, safe="/:=' ") + '")'
        out.append(f".i-{name}{{-webkit-mask-image:{url};mask-image:{url}}}")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# animations — every keyframe exists twice (A / B). When a page re-renders the wrapper
# flips between .pg-a and .pg-b, which restarts every entrance animation inside it.
# --------------------------------------------------------------------------- #
_KF = {
    "fadeUp": "from{opacity:0;transform:translateY(12px)}",
    "fade": "from{opacity:0}",
    "wipeX": "from{clip-path:inset(-20px 100% -20px -20px)}",
    "wipeY": "from{clip-path:inset(100% -20px -20px -20px)}",
    "spinIn": "from{opacity:0;transform:rotate(-80deg) scale(.86)}",
    "growW": "from{width:0}",
    "growH": "from{height:0}",
    "ring": "from{--p:0}",
    "count": "from{--n:0}",
}
_EASE = "cubic-bezier(.22,1,.36,1)"
# class → (keyframe, duration/easing)
_CLASSES = {
    "rise": ("fadeUp", f".5s {_EASE}"),
    "fade": ("fade", ".5s ease"),
    "wipe-x": ("wipeX", "1.25s cubic-bezier(.45,.05,.2,1)"),
    "wipe-y": ("wipeY", "1s cubic-bezier(.45,.05,.2,1)"),
    "spin-in": ("spinIn", "1.1s " + _EASE),
    "grow-w": ("growW", "1s " + _EASE),
    "grow-h": ("growH", "1s " + _EASE),
    "ring": ("ring", "1.4s " + _EASE),
    "count": ("count", "1.2s " + _EASE),
}


def _anim_css() -> str:
    css = []
    for name, body in _KF.items():
        for v in "ABCD":
            css.append(f"@keyframes {name}{v}{{{body}}}")
    for cls, (kf, timing) in _CLASSES.items():
        for v in "ab":
            css.append(f".pg-{v} .{cls}{{animation:{kf}{v.upper()} {timing} backwards;animation-delay:var(--d,0ms)}}")
    for cls, (kf, timing) in _CLASSES.items():
        for v, k in (("a", "C"), ("b", "D")):
            css.append(f".app .{cls}.dyn-{v}{{animation:{kf}{k} {timing} backwards;animation-delay:var(--d,0ms)}}")
    css.append(f".pg-a{{animation:fadeUpA .4s {_EASE} backwards}}.pg-b{{animation:fadeUpB .4s {_EASE} backwards}}")
    return "\n".join(css)


FONTS = ("https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800"
         "&family=Space+Grotesk:wght@500;600;700&display=swap")

BASE_CSS = r"""
@property --p{syntax:'<number>';initial-value:0;inherits:false}
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
:root{--bg:#0a120e;--ink:#e9f2ea;--muted:#9cb3a4;--dim:#67806f;--line:rgba(255,255,255,.09);
--moss:#7fb48d;--moss-strong:#a9d6b0;--amber:#d9a45b;--clay:#d07a63;--blue:#7fb0c9;
--font-disp:"Space Grotesk","Manrope",sans-serif;--font-ui:"Manrope","Space Grotesk",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;font-family:var(--font-ui);background:var(--bg);color:var(--ink);font-size:14px;
letter-spacing:.01em;overflow:hidden;-webkit-font-smoothing:antialiased}
#react-entry-point,#_dash-app-content{height:100%}
a{color:inherit;text-decoration:none}
button{font-family:inherit;cursor:pointer;border:0;background:none;color:inherit;padding:0}
p,h1,h2,h3{margin:0}
::selection{background:rgba(127,180,141,.32);color:#f2faf4}
*::-webkit-scrollbar{width:9px;height:9px}*::-webkit-scrollbar-track{background:transparent}
*::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:99px;border:2px solid transparent;background-clip:content-box}
*::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.22);border:2px solid transparent;background-clip:content-box}
*{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.16) transparent}
:focus-visible{outline:2px solid rgba(127,180,141,.65);outline-offset:2px;border-radius:6px}

/* backdrop */
.atmosphere{position:fixed;inset:0;z-index:0;pointer-events:none;background:
radial-gradient(1100px 700px at 12% -8%,rgba(97,168,122,.17),transparent 60%),
radial-gradient(900px 620px at 88% 4%,rgba(58,122,88,.13),transparent 62%),
radial-gradient(1500px 1000px at 50% 118%,rgba(30,72,50,.5),transparent 65%),
linear-gradient(175deg,#0c1510 0%,#0a120d 48%,#081009 100%)}
.atmosphere::before{content:"";position:absolute;inset:-20%;
background:radial-gradient(700px 460px at 30% 20%,rgba(122,190,145,.075),transparent 70%);
animation:breathe 26s ease-in-out infinite alternate}
.atmosphere::after{content:"";position:absolute;inset:0;opacity:.05;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E")}
@keyframes breathe{from{transform:translate3d(-2%,-1%,0) scale(1);opacity:.7}to{transform:translate3d(3%,4%,0) scale(1.12);opacity:1}}
@keyframes pulseDot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.45;transform:scale(.8)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes scaleIn{from{opacity:0;transform:scale(.965) translateY(8px)}to{opacity:1;transform:none}}
@keyframes drawerIn{from{opacity:0;transform:translateX(36px)}to{opacity:1;transform:none}}
@keyframes toastIn{from{opacity:0;transform:translateX(18px) scale(.97)}to{opacity:1;transform:none}}
@keyframes toastOut{to{opacity:0;transform:translateX(18px);visibility:hidden}}
@keyframes spin{to{transform:rotate(360deg)}}

/* glass */
.glass{background:linear-gradient(165deg,rgba(255,255,255,.065),rgba(255,255,255,.028));border:1px solid rgba(255,255,255,.09);
backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-radius:12px;
box-shadow:0 14px 34px -18px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.05)}
.glass-nav{background:rgba(11,20,15,.58);border-right:1px solid rgba(255,255,255,.07);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px)}
.glass-top{background:rgba(10,18,13,.42);border-bottom:1px solid rgba(255,255,255,.06);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
.glass-pop{background:rgba(14,24,18,.9);border:1px solid rgba(255,255,255,.1);backdrop-filter:blur(26px) saturate(1.15);-webkit-backdrop-filter:blur(26px) saturate(1.15);box-shadow:0 30px 70px -20px rgba(0,0,0,.7)}
.glass-inset{background:rgba(6,12,9,.32);border:1px solid rgba(255,255,255,.06);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px)}
.glass-chip{background:rgba(9,16,12,.94);border:1px solid rgba(255,255,255,.11);backdrop-filter:blur(16px);box-shadow:0 12px 30px -12px rgba(0,0,0,.65)}
.card-hover{transition:border-color .25s ease,background .25s ease,transform .25s ease,box-shadow .25s ease;cursor:pointer}
.card-hover:hover{border-color:rgba(255,255,255,.17);background:linear-gradient(165deg,rgba(255,255,255,.085),rgba(255,255,255,.04));
transform:translateY(-2px);box-shadow:0 20px 44px -18px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.07)}
.lift{transition:transform .2s ease,background .2s ease,border-color .2s ease}
.lift:hover{transform:translateY(-2px);background:rgba(255,255,255,.07)}

/* typography */
.disp{font-family:var(--font-disp)}
.num{font-family:var(--font-disp);font-feature-settings:"tnum" 1,"lnum" 1;letter-spacing:-.015em}
.eyebrow{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.sub{font-size:12px;color:var(--muted)}
.t-r{text-align:right}.t-c{text-align:center}
.ellipsis{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.clamp2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* icons */
.ico{display:inline-block;flex:none;background-color:currentColor;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;
-webkit-mask-position:center;mask-position:center;-webkit-mask-size:contain;mask-size:contain;vertical-align:middle}

/* layout */
.app{position:relative;z-index:10;height:100vh;display:flex}
.side{width:224px;flex:none;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:10px;padding:20px 16px 16px}
.brand-mark{width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,#8fc49b,#4c8a63);display:flex;align-items:center;justify-content:center;
color:#0b1712;box-shadow:0 8px 20px -6px rgba(127,180,141,.5);transition:transform .3s}
.brand:hover .brand-mark{transform:scale(1.07) rotate(-4deg)}
.brand-name{font-family:var(--font-disp);font-size:15px;font-weight:700;color:#f0f7f2;line-height:1;letter-spacing:-.01em;display:block}
.brand-sub{font-size:9.5px;text-transform:uppercase;letter-spacing:.22em;color:#6f8878;font-weight:700;margin-top:4px;display:block}
.nav{flex:1;padding:0 10px;display:flex;flex-direction:column;gap:2px;overflow-y:auto}
.nav-item{position:relative;display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;font-size:13px;font-weight:600;
color:#8ba293;transition:all .2s}
.nav-item .ico{color:#6f8878;transition:color .2s,transform .2s}
.nav-item:hover{color:#d3e3d7;background:rgba(255,255,255,.05)}
.nav-item:hover .ico{transform:scale(1.12)}
.nav-item.active{background:rgba(255,255,255,.09);color:#f0f7f2;box-shadow:inset 0 1px 0 rgba(255,255,255,.07)}
.nav-item.active .ico{color:#a9d6b0}
.nav-item.active::before{content:"";position:absolute;left:0;top:50%;transform:translateY(-50%);width:3px;height:18px;border-radius:99px;background:#8fc49b;animation:fadeIn .4s}
.side-foot{padding:14px 16px;border-top:1px solid rgba(255,255,255,.06);display:flex;align-items:center;gap:8px}
.live-dot{width:8px;height:8px;border-radius:50%;background:#8fc49b;animation:pulseDot 2.4s ease-in-out infinite}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.topbar{height:56px;flex:none;display:flex;align-items:center;padding:0 20px;gap:16px}
.topbar h1{font-family:var(--font-disp);font-size:15px;font-weight:700;color:#f0f7f2;letter-spacing:-.01em;line-height:1}
.topbar p{font-size:11px;color:#7d9485;margin-top:4px}
.content{flex:1;min-height:0;overflow-y:auto}
.page{padding:20px;max-width:1480px;margin:0 auto;width:100%;display:flex;flex-direction:column;gap:16px}
.row-flex{display:flex;align-items:center}
.gap8{gap:8px}.gap12{gap:12px}.ml-auto{margin-left:auto}
.wrap{flex-wrap:wrap}

/* grids */
.grid{display:grid;gap:16px}
.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
.g12{grid-template-columns:repeat(12,minmax(0,1fr))}
.g12>*{grid-column:span 12;min-width:0}
@media(min-width:1024px){.g12>.lg3{grid-column:span 3}.g12>.lg4{grid-column:span 4}.g12>.lg5{grid-column:span 5}.g12>.lg6{grid-column:span 6}.g12>.lg7{grid-column:span 7}}
@media(min-width:1280px){.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}
.g12>.xl4{grid-column:span 4}.g12>.xl5{grid-column:span 5}.g12>.xl6{grid-column:span 6}.g12>.xl7{grid-column:span 7}.g12>.xl8{grid-column:span 8}}
.cols-1-2{grid-template-columns:1fr}
@media(min-width:1280px){.cols-1-2{grid-template-columns:repeat(2,minmax(0,1fr))}.cols-1-3{grid-template-columns:repeat(3,minmax(0,1fr))}}
.cols-rec{grid-template-columns:1fr;gap:12px}
@media(min-width:768px){.cols-rec{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1280px){.cols-rec{grid-template-columns:repeat(4,minmax(0,1fr))}}
.cols-3{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.cols-4{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.cols-2{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.span2{grid-column:span 2}

/* cards */
.card{padding:16px}.card-lg{padding:20px}
.shead{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:12px}
.shead h3{font-family:var(--font-disp);font-size:15px;font-weight:600;color:#e9f2ea;letter-spacing:-.01em}
.shead p{font-size:12px;color:#9cb3a4;margin-top:2px}
.stat{padding:14px;display:flex;align-items:center;gap:12px}
.stat-ico{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#8fc49b}
.stat .v{font-size:19px;font-weight:600;color:#f2f8f3;line-height:1.2}
.kpi{padding:16px;display:flex;flex-direction:column;gap:10px;color:inherit}
.kpi-top{display:flex;align-items:center;justify-content:space-between;color:#5f7466}
.kpi-body{display:flex;align-items:flex-end;justify-content:space-between;gap:8px}
.kpi-val{font-size:25px;font-weight:600;color:#f2f8f3;line-height:1}
.kpi-sub{font-size:11px;color:#7d9485;margin-top:6px}
.kpi-spark{width:108px;height:40px;flex:none;opacity:.95}
.baseline{display:flex;align-items:baseline;gap:8px}
.delta{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:700}
.delta.good{color:#a9d6b0}.delta.bad{color:#e4bd83}.delta.flat{color:#7d9485}

/* count-up numbers (pure CSS) */
.count{--n:var(--to);counter-reset:cn var(--n)}
.count::after{content:counter(cn)}

/* buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border-radius:8px;font-weight:600;font-size:13px;padding:8px 14px;
transition:all .2s;user-select:none;white-space:nowrap}
.btn:active{transform:scale(.97)}
.btn.sm{font-size:12px;padding:6px 10px;gap:6px}
.btn-primary{background:#7fb48d;color:#0a1410;box-shadow:0 10px 24px -10px rgba(127,180,141,.55)}
.btn-primary:hover{background:#95c6a4;transform:translateY(-1px);box-shadow:0 14px 28px -10px rgba(127,180,141,.7)}
.btn-soft{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);color:#e9f2ea}
.btn-soft:hover{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.2)}
.btn-ghost{color:#9cb3a4}.btn-ghost:hover{color:#e9f2ea;background:rgba(255,255,255,.06)}
.btn-danger{background:rgba(208,122,99,.12);border:1px solid rgba(208,122,99,.35);color:#e29381}
.btn-danger:hover{background:rgba(208,122,99,.22)}
.btn.flex1{flex:1}
.btn:disabled{opacity:.4;pointer-events:none}
.link-moss{font-size:12px;font-weight:600;color:#8fc49b;transition:color .2s}.link-moss:hover{color:#a9d6b0}
.icon-btn{width:32px;height:32px;border-radius:8px;color:#7d9485;display:inline-flex;align-items:center;justify-content:center;transition:all .2s}
.icon-btn:hover{color:#e9f2ea;background:rgba(255,255,255,.08)}
.step-btn{width:36px;height:36px;border-radius:8px;color:#9cb3a4;display:inline-flex;align-items:center;justify-content:center;transition:color .2s,transform .15s;flex:none}
.step-btn:hover{color:#e9f2ea}.step-btn:active{transform:scale(.92)}

/* pills */
.pill{display:inline-flex;align-items:center;gap:6px;border-radius:99px;border:1px solid;padding:3px 8px;font-size:11px;font-weight:600;white-space:nowrap}
.pill.ok{color:#a9d6b0;background:rgba(127,180,141,.12);border-color:rgba(127,180,141,.28)}
.pill.warn{color:#e4bd83;background:rgba(217,164,91,.12);border-color:rgba(217,164,91,.3)}
.pill.crit{color:#e29381;background:rgba(208,122,99,.14);border-color:rgba(208,122,99,.38)}
.pill.info{color:#9cc4d8;background:rgba(127,176,201,.12);border-color:rgba(127,176,201,.3)}
.pill.neutral{color:#9cb3a4;background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.12)}
.pill .dot{width:6px;height:6px;border-radius:50%;background:currentColor;animation:pulseDot 2.2s ease-in-out infinite}
.pill.w24{width:24px;justify-content:center;padding:3px 0}

/* bars */
.bar{height:5px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;width:100%}
.bar.thick{height:6px}
.fill{height:100%;border-radius:99px;width:var(--w,0%);transition:filter .2s}
.fill.ok{background:#7fb48d}.fill.warn{background:#d9a45b}.fill.crit{background:#d07a63}
.fill.grad-ok{background:linear-gradient(90deg,#4c8a63,#8fc49b)}.fill.grad-warn{background:linear-gradient(90deg,#d9a45b,#e4bd83)}
.hrow:hover .fill{filter:brightness(1.25)}

/* ring (conic gradient, animated with @property) */
.ring{--c:#7fb48d;width:var(--size,128px);height:var(--size,128px);border-radius:50%;--p:var(--score);
background:conic-gradient(var(--c) calc(var(--p)*1%),rgba(255,255,255,.08) 0);
-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 9px),#000 calc(100% - 8px));mask:radial-gradient(farthest-side,transparent calc(100% - 9px),#000 calc(100% - 8px))}
.ring.warn{--c:#d9a45b}.ring.crit{--c:#d07a63}
.ring-wrap{position:relative;width:var(--size,128px);height:var(--size,128px);flex:none}
.ring-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring-center .big{font-size:30px;font-weight:600}
.ring-center .cap{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:#7d9485;font-weight:700}

/* donut */
.donut-wrap{position:relative;height:250px}
.donut-wrap .dg{height:100%}
.donut-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none}
.donut-center .big{font-size:22px;font-weight:600;color:#f2f8f3}
.legend{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.legend-row{display:flex;align-items:center;gap:8px;font-size:12px;width:100%;padding:3px 4px;border-radius:6px;transition:background .2s}
.legend-row:hover{background:rgba(255,255,255,.06)}
.legend-row .sw{width:10px;height:10px;border-radius:4px;flex:none;transition:transform .2s}
.legend-row:hover .sw{transform:scale(1.35)}
.legend-row .nm{color:#9cb3a4;transition:color .2s}.legend-row:hover .nm{color:#e9f2ea}

/* tooltips for html bars */
.tip{position:relative}
.tip[data-tip]:hover::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);white-space:nowrap;
font-size:11px;font-weight:600;color:#e9f2ea;padding:5px 9px;border-radius:8px;background:rgba(9,16,12,.96);border:1px solid rgba(255,255,255,.12);
box-shadow:0 12px 30px -12px rgba(0,0,0,.7);z-index:30;pointer-events:none;animation:fadeIn .15s}

/* list rows */
.hrow{display:flex;align-items:center;gap:12px;width:100%;padding:5px 4px;border-radius:8px;transition:background .2s;text-align:left}
.hrow:hover{background:rgba(255,255,255,.045)}
.hrow .nm{font-size:12px;color:#c5d6c9;transition:color .2s;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hrow:hover .nm{color:#e9f2ea}
.hrow .grow{flex:1;min-width:30px}
.val-s{font-size:11px;color:#9cb3a4}

/* alerts */
.alert-card{display:block;width:100%;text-align:left;border-radius:8px;padding:10px;transition:background .2s,transform .2s}
.alert-card:hover{background:rgba(255,255,255,.07);transform:translateX(2px)}
.alert-card p{font-size:11.5px;color:#c5d6c9;line-height:1.35;margin-top:6px;transition:color .2s}
.alert-card:hover p{color:#e9f2ea}
.stack{display:flex;flex-direction:column;gap:8px}.stack6{display:flex;flex-direction:column;gap:6px}.stack16{display:flex;flex-direction:column;gap:16px}

/* rec tiles */
.rec{display:block;border-radius:12px;padding:14px;text-align:left}
.rec .ric{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;border:1px solid}
.ric.crit{background:rgba(208,122,99,.14);border-color:rgba(208,122,99,.35);color:#e29381}
.ric.warn{background:rgba(217,164,91,.13);border-color:rgba(217,164,91,.3);color:#e4bd83}
.ric.info{background:rgba(127,176,201,.12);border-color:rgba(127,176,201,.3);color:#9cc4d8}
.rec .hd{font-size:12.5px;font-weight:600;color:#e9f2ea;line-height:1.35}
.rec .ac{font-size:11px;color:#7d9485;margin-top:6px}
.rec .ext{margin-left:auto;color:#5f7466;transition:color .2s,transform .2s}
.rec:hover .ext{color:#8fc49b;transform:translate(2px,-2px)}

/* decision cards */
.dec{padding:16px;display:flex;flex-direction:column;border-left:3px solid}
.dec.critical{border-left-color:#d07a63}.dec.warning{border-left-color:#d9a45b}.dec.opportunity,.dec.info{border-left-color:#7fb0c9}
.dec .ico-box{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.dec ul{list-style:none;margin:8px 0 0;padding:0;display:flex;flex-direction:column;gap:6px;flex:1}
.dec li{display:flex;gap:8px;font-size:11.5px;color:#9cb3a4;line-height:1.35}
.dec li::before{content:"";margin-top:6px;width:4px;height:4px;border-radius:50%;background:#5f7466;flex:none}
.metric{display:inline-block;border-radius:6px;padding:4px 8px;font-size:10.5px;color:#9cb3a4}
.metric b{font-family:var(--font-disp);color:#dceade;margin-left:4px}
.dec-foot{display:flex;gap:8px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.06);align-items:center}
.t-crit{color:#e29381}.t-warn{color:#e4bd83}.t-ok{color:#a9d6b0}.t-info{color:#9cc4d8}

/* inputs */
.inp,input.inp{width:100%;border-radius:8px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.11);padding:8px 12px;
font-size:13px;color:#e9f2ea;font-family:var(--font-ui);transition:border-color .2s,background .2s;outline:none;height:38px}
.inp::placeholder{color:#5f7466}
.inp:focus{border-color:rgba(127,180,141,.6);background:rgba(255,255,255,.08)}
.inp.num{font-family:var(--font-disp)}
.search{position:relative}
.search .ico{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#67806f;pointer-events:none;z-index:2}
.search .inp{padding-left:36px}
input[type=number]{-moz-appearance:textfield}
input[type=number]::-webkit-inner-spin-button{opacity:.3}
.field{display:block}
.field .eyebrow{display:block;margin-bottom:6px}
.field .hint{display:block;margin-top:4px;font-size:11px;color:#67806f}
input[type=range]{-webkit-appearance:none;appearance:none;height:4px;border-radius:99px;background:rgba(255,255,255,.12);width:100%;padding:0;border:0}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:14px;height:14px;border-radius:50%;background:var(--moss);border:2px solid #0c1511;box-shadow:0 0 0 1px rgba(127,180,141,.5);cursor:pointer;transition:transform .15s}
input[type=range]::-webkit-slider-thumb:hover{transform:scale(1.3)}
input[type=range]::-moz-range-thumb{width:12px;height:12px;border-radius:50%;background:var(--moss);border:2px solid #0c1511;cursor:pointer}

/* segmented controls + chips (dcc.RadioItems) */
.seg{display:inline-flex;padding:3px;border-radius:8px;background:rgba(6,12,9,.32);border:1px solid rgba(255,255,255,.06);gap:0}
.seg label{margin:0;cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;color:#7d9485;transition:all .2s;display:inline-block!important}
.seg label:hover{color:#c5d6c9}
.seg input{display:none}
.seg label:has(input:checked){background:rgba(255,255,255,.13);color:#e9f2ea;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}
.chips{display:flex;gap:4px;flex-wrap:wrap}
.chips label{margin:0;cursor:pointer;padding:4px 10px;border-radius:99px;font-size:11px;font-weight:700;border:1px solid rgba(255,255,255,.1);color:#7d9485;transition:all .2s;display:inline-block!important}
.chips label:hover{color:#c5d6c9;border-color:rgba(255,255,255,.2)}
.chips input{display:none}
.chips label:has(input:checked){background:rgba(127,180,141,.16);border-color:rgba(127,180,141,.4);color:#b3dcb9}

/* dropdown (dcc.Dropdown / react-select) */
.dd{min-width:150px}
.dd .Select-control{background:rgba(255,255,255,.055)!important;border:1px solid rgba(255,255,255,.11)!important;border-radius:8px!important;height:38px;transition:border-color .2s,background .2s}
.dd .Select-control:hover{box-shadow:none!important;border-color:rgba(255,255,255,.2)!important}
.dd.is-open .Select-control,.dd .is-focused .Select-control,.dd .Select.is-focused>.Select-control{border-color:rgba(127,180,141,.6)!important;background:rgba(255,255,255,.08)!important}
.dd .Select-value-label,.dd .Select--single>.Select-control .Select-value .Select-value-label{color:#e9f2ea!important;font-size:13px}
.dd .Select-placeholder{color:#5f7466!important;font-size:13px;line-height:36px}
.dd .Select-value,.dd .Select-placeholder{line-height:36px!important}
.dd .Select-input{height:36px}.dd .Select-input>input{color:#e9f2ea;line-height:20px;padding:8px 0}
.dd .Select-arrow{border-top-color:#67806f!important}
.dd .Select-menu-outer{background:rgba(12,21,15,.97)!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:10px!important;margin-top:6px;
box-shadow:0 24px 50px -14px rgba(0,0,0,.8);overflow:hidden;z-index:50;animation:scaleIn .18s}
.dd .Select-menu-outer *{color:#c5d6c9}
.dd .VirtualizedSelectOption,.dd .Select-option{background:transparent!important;font-size:13px;padding:8px 12px;cursor:pointer;transition:background .15s}
.dd .VirtualizedSelectFocusedOption,.dd .Select-option.is-focused{background:rgba(255,255,255,.08)!important}
.dd .VirtualizedSelectSelectedOption,.dd .Select-option.is-selected{background:rgba(127,180,141,.16)!important;color:#b3dcb9!important}
.dd .Select-noresults{color:#67806f;padding:10px 12px}

/* grid-based tables */
.tscroll{max-height:52vh;overflow-y:auto;margin:0 -4px}
.trow{display:grid;grid-template-columns:var(--cols);align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid rgba(255,255,255,.05);transition:background .16s;position:relative}
.trow.link{cursor:pointer}
.trow:hover{background:rgba(255,255,255,.045)}
.thead{position:sticky;top:0;z-index:5;background:rgba(12,21,15,.92);backdrop-filter:blur(10px);cursor:default;padding:10px 14px;
font-size:10.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--line)}
.thead:hover{background:rgba(12,21,15,.92)}
.thead button{font:inherit;letter-spacing:inherit;text-transform:inherit;color:inherit;display:inline-flex;align-items:center;gap:4px;transition:color .2s}
.thead button:hover{color:#c5d6c9}
#inv-head,#inv-body,#sl-body{display:contents}
.tname{font-size:13px;font-weight:600;color:#e9f2ea;line-height:1.25}
.tsub{font-size:11px;color:#7d9485;margin-top:2px}
.tc{font-size:13px;color:#c5d6c9}
.stock-cell{display:flex;align-items:center;gap:8px}
.stock-cell .n{width:30px;text-align:right;font-size:13px;font-weight:600}
.u{font-size:10px;color:#67806f}
details.sale>summary{list-style:none;cursor:pointer}
details.sale>summary::-webkit-details-marker{display:none}
details.sale .chev{transition:transform .25s;color:#5f7466}
details.sale[open] .chev{transform:rotate(90deg)}
details.sale .more{margin:4px 8px 8px;border-radius:8px;padding:12px 16px;display:flex;flex-wrap:wrap;align-items:center;gap:8px 24px;animation:fadeIn .3s}
.more .k{font-size:11px;color:#7d9485}.more .k b{font-family:var(--font-disp);color:#a9d6b0;margin-left:4px}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 16px;text-align:center;gap:8px}
.empty .eb{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#8fc49b;margin-bottom:4px}
.empty h4{margin:0;font-size:14px;color:#e9f2ea}.empty p{font-size:12px;color:#7d9485}

/* weekly rhythm */
.week{display:flex;align-items:flex-end;gap:8px;height:190px;padding:8px 4px 0}
.wcol{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;height:100%;justify-content:flex-end}
.wbar{width:100%;border-radius:6px 6px 0 0;height:var(--h);background:linear-gradient(180deg,rgba(143,196,155,.5),rgba(143,196,155,.12));transition:filter .2s,transform .2s;transform-origin:bottom}
.wbar.peak{background:linear-gradient(180deg,rgba(143,196,155,.9),rgba(143,196,155,.25))}
.wcol:hover .wbar{filter:brightness(1.35);transform:scaleY(1.03)}
.wcol .n{font-size:11px;font-weight:600;color:#7d9485;transition:color .2s}.wcol:hover .n,.wcol .n.peak{color:#a9d6b0}
.wcol .d{font-size:10px;color:#7d9485;font-weight:700}

/* overlays */
.overlay{position:fixed;inset:0;z-index:60}
.backdrop{position:absolute;inset:0;background:rgba(4,9,6,.62);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);animation:fadeIn .25s;cursor:default}
.overlay.center{display:flex;align-items:center;justify-content:center;padding:20px}
.modal{position:relative;width:100%;max-width:560px;border-radius:16px;animation:scaleIn .32s cubic-bezier(.22,1,.36,1) both}
.modal-head{display:flex;align-items:center;gap:12px;padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.07)}
.modal-head h2{font-family:var(--font-disp);font-size:15px;font-weight:600;color:#e9f2ea}
.modal-ico{width:32px;height:32px;border-radius:8px;background:rgba(127,180,141,.14);border:1px solid rgba(127,180,141,.25);color:#a9d6b0;display:flex;align-items:center;justify-content:center}
.modal-body{padding:16px 20px}
.modal-foot{padding:14px 20px;border-top:1px solid rgba(255,255,255,.07);display:flex;justify-content:flex-end;gap:8px;background:rgba(255,255,255,.02);border-radius:0 0 16px 16px}
.drawer{position:absolute;right:0;top:0;height:100%;width:min(480px,94vw);overflow-y:auto;border-left:1px solid rgba(255,255,255,.1);animation:drawerIn .34s cubic-bezier(.22,1,.36,1) both}
.drawer-head{position:sticky;top:0;z-index:10;padding:16px 20px;display:flex;align-items:center;gap:12px;background:rgba(14,24,18,.95);border-bottom:1px solid rgba(255,255,255,.06)}
.drawer-body{padding:16px 20px;display:flex;flex-direction:column;gap:16px}
.rec-box{border-radius:12px;border:1px solid rgba(217,164,91,.3);background:rgba(217,164,91,.07);padding:14px}
.mini{border-radius:8px;padding:10px}
.mini .v{font-size:15px;font-weight:600;color:#e9f2ea;margin-top:4px}
.move{display:flex;align-items:center;gap:10px;border-radius:8px;padding:8px 12px}

/* toasts */
.toasts{position:fixed;top:16px;right:16px;z-index:80;display:flex;flex-direction:column;gap:8px;width:320px;pointer-events:none}
.toast{border-radius:12px;padding:12px 14px;display:flex;gap:10px;border:1px solid;animation:toastIn .3s cubic-bezier(.22,1,.36,1) both,toastOut .4s ease 4.6s forwards}
.toast.ok{border-color:rgba(127,180,141,.4)}.toast.warn{border-color:rgba(217,164,91,.4)}.toast.crit{border-color:rgba(208,122,99,.45)}.toast.info{border-color:rgba(127,176,201,.4)}
.toast b{font-size:13px;font-weight:600;color:#e9f2ea;display:block;line-height:1.3}
.toast span.d{font-size:12px;color:#9cb3a4;display:block;margin-top:2px;line-height:1.3}

/* graphs */
.js-plotly-plot .plotly .modebar{display:none!important}
.js-plotly-plot .plotly .main-svg{overflow:visible!important}
.hint-line{height:36px;display:flex;align-items:center;padding:0 4px;margin-top:8px;font-size:11px;color:#5f7466}
.detail-line{display:flex;align-items:center;gap:12px;font-size:12px;color:#9cb3a4;animation:fadeIn .4s}
.detail-line .dot{width:6px;height:6px;border-radius:50%;background:#8fc49b}
.legend-inline{display:flex;align-items:center;gap:16px;margin-top:4px;padding:0 4px}
.legend-inline span{display:flex;align-items:center;gap:6px;font-size:11px;color:#7d9485}
.line-sw{width:12px;height:3px;border-radius:3px;background:#8fc49b}
.line-sw.dash{background:none;border-top:2px dashed #5f7a6b;height:0}
.about p{display:flex;align-items:center;gap:8px;font-size:12px;color:#9cb3a4;margin:0 0 10px}
.about .ico{color:#8fc49b}
.cls-box{flex:1;border-radius:8px;padding:8px 12px}
.cls-box .v{font-size:16px;font-weight:600;color:#e9f2ea;margin-top:4px}
.dotc{width:8px;height:8px;border-radius:50%;display:inline-block}
"""

CSS = BASE_CSS + "\n/* icons */\n" + _icon_css() + "\n/* animations */\n" + _anim_css()
