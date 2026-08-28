/* @ds-bundle: {"format":4,"namespace":"KeelDesignSystem_7d5998","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Chip","sourcePath":"components/core/Chip.jsx"},{"name":"Dot","sourcePath":"components/core/Dot.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"CoverageBar","sourcePath":"components/data/CoverageBar.jsx"},{"name":"DiffView","sourcePath":"components/data/DiffView.jsx"},{"name":"FacetPanel","sourcePath":"components/data/FacetPanel.jsx"},{"name":"GapChips","sourcePath":"components/data/GapChips.jsx"},{"name":"SeveritySpine","sourcePath":"components/data/RiskBadge.jsx"},{"name":"RiskBadge","sourcePath":"components/data/RiskBadge.jsx"},{"name":"SplitBar","sourcePath":"components/data/SplitBar.jsx"},{"name":"StatTile","sourcePath":"components/data/StatTile.jsx"},{"name":"EmptyState","sourcePath":"components/feedback/EmptyState.jsx"},{"name":"ErrorSummary","sourcePath":"components/feedback/ErrorSummary.jsx"},{"name":"SavedDialog","sourcePath":"components/feedback/SavedDialog.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"WarnBanner","sourcePath":"components/feedback/WarnBanner.jsx"},{"name":"CheckSet","sourcePath":"components/forms/CheckSet.jsx"},{"name":"Field","sourcePath":"components/forms/Field.jsx"},{"name":"SearchInput","sourcePath":"components/forms/SearchInput.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"TextArea","sourcePath":"components/forms/TextArea.jsx"},{"name":"TextInput","sourcePath":"components/forms/TextInput.jsx"},{"name":"Breadcrumb","sourcePath":"components/structure/Breadcrumb.jsx"},{"name":"Card","sourcePath":"components/structure/Card.jsx"},{"name":"EditorCard","sourcePath":"components/structure/EditorCard.jsx"},{"name":"EntityHeader","sourcePath":"components/structure/EntityHeader.jsx"},{"name":"RailRow","sourcePath":"components/structure/RailRow.jsx"},{"name":"ScreenTabs","sourcePath":"components/structure/ScreenTabs.jsx"},{"name":"SectionBand","sourcePath":"components/structure/SectionBand.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"5b0a4931bcee","components/core/Button.jsx":"510b3904de91","components/core/Chip.jsx":"71ac2692014d","components/core/Dot.jsx":"d3dacfd80544","components/core/IconButton.jsx":"0482679ca95e","components/data/CoverageBar.jsx":"f21f26b0efd3","components/data/DiffView.jsx":"d94d6014db36","components/data/FacetPanel.jsx":"623c9769bb0d","components/data/GapChips.jsx":"748007c6989b","components/data/RiskBadge.jsx":"53029e941621","components/data/SplitBar.jsx":"c193380995b5","components/data/StatTile.jsx":"59c3cb89c0a7","components/feedback/EmptyState.jsx":"7278d47ce681","components/feedback/ErrorSummary.jsx":"e8a599354d09","components/feedback/SavedDialog.jsx":"39a9bdea7396","components/feedback/Toast.jsx":"df1ac229c05d","components/feedback/WarnBanner.jsx":"03bcd169c28a","components/forms/CheckSet.jsx":"354b69d60dc1","components/forms/Field.jsx":"af3b7e964b3c","components/forms/SearchInput.jsx":"6b3ec8c52391","components/forms/Select.jsx":"157805bbe5b3","components/forms/TextArea.jsx":"6900b5667299","components/forms/TextInput.jsx":"3aafecfee632","components/structure/Breadcrumb.jsx":"36609ff9661a","components/structure/Card.jsx":"35f138eb0947","components/structure/EditorCard.jsx":"06d074aca2f5","components/structure/EntityHeader.jsx":"e4fe64806eba","components/structure/RailRow.jsx":"3f14d4427c70","components/structure/ScreenTabs.jsx":"439a4e0fe295","components/structure/SectionBand.jsx":"93591eb3ff90","ui_kits/authoring-ui/MitigationsScreen.jsx":"58f99f9ce4c6","ui_kits/authoring-ui/OverviewScreen.jsx":"e82662cf89ae","ui_kits/authoring-ui/ReportsScreen.jsx":"c694d7ec1260","ui_kits/authoring-ui/StyleGuideScreen.jsx":"058018886280","ui_kits/authoring-ui/ThreatsScreen.jsx":"904620195bcc","ui_kits/authoring-ui/app.jsx":"a367230b4879","ui_kits/authoring-ui/data.js":"b29d351e1ee2","ui_kits/authoring-ui/shell.jsx":"c4d33c46e2f9"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.KeelDesignSystem_7d5998 = window.KeelDesignSystem_7d5998 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const TONES = {
  soft: {
    bg: "var(--navy-100)",
    fg: "var(--navy-600)",
    weight: "var(--fw-medium)",
    radius: "var(--r-pill)"
  },
  type: {
    bg: "var(--navy-200)",
    fg: "var(--navy-700)"
  },
  harm: {
    bg: "var(--crimson-600)",
    fg: "#fff"
  },
  danger: {
    bg: "var(--crimson-50)",
    fg: "var(--crimson-700)"
  },
  ok: {
    bg: "var(--green-50)",
    fg: "var(--green)"
  },
  advice: {
    bg: "var(--amber-50)",
    fg: "var(--amber)"
  },
  orphan: {
    bg: "var(--navy-200)",
    fg: "var(--navy-600)"
  }
};

/** A word in a coloured pill. Keel says the word rather than drawing a symbol. */
function Badge({
  tone = "soft",
  numeric,
  mono,
  children,
  style,
  ...rest
}) {
  const t = TONES[tone] || TONES.soft;
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
      fontSize: "var(--fs-10)",
      padding: "1px 8px",
      borderRadius: t.radius || "var(--r-4)",
      fontWeight: t.weight || "var(--fw-semibold)",
      whiteSpace: "nowrap",
      background: t.bg,
      color: t.fg,
      fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
      fontVariantNumeric: numeric ? "var(--numeric)" : "normal",
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
const SIZES = {
  md: {
    padding: "7px 13px",
    fontSize: "var(--fs-13)"
  },
  sm: {
    padding: "4px 9px",
    fontSize: "var(--fs-12)"
  }
};
const FILLS = {
  primary: {
    rest: "var(--crimson-600)",
    hover: "var(--crimson-700)",
    fg: "#fff"
  },
  ghost: {
    rest: "var(--navy-100)",
    hover: "var(--navy-200)",
    fg: "var(--navy-700)"
  },
  bare: {
    rest: "transparent",
    hover: "var(--navy-100)",
    fg: "var(--navy-700)"
  }
};

/** Keel's only button. Crimson fill = the one primary action on a screen. */
function Button({
  variant = "ghost",
  size = "md",
  disabled,
  glyph,
  children,
  style,
  ...rest
}) {
  const [hover, setHover] = useState(false);
  const f = FILLS[variant] || FILLS.ghost;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    disabled: disabled,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
      whiteSpace: "nowrap",
      border: "1px solid transparent",
      borderRadius: "var(--r-8)",
      fontFamily: "var(--font-sans)",
      fontWeight: "var(--fw-semibold)",
      lineHeight: 1.4,
      cursor: disabled ? "default" : "pointer",
      background: disabled || !hover ? f.rest : f.hover,
      color: f.fg,
      opacity: disabled ? 0.5 : 1,
      ...SIZES[size],
      ...style
    }
  }, rest), glyph ? /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true"
  }, glyph) : null, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Chip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** A multi-select filter chip, or a clickable jump chip. Selected = solid crimson. */
function Chip({
  selected,
  variant = "facet",
  mono,
  children,
  style,
  ...rest
}) {
  const [hover, setHover] = useState(false);
  const jump = variant === "jump";
  const base = {
    fontFamily: mono || jump ? "var(--font-mono)" : "var(--font-sans)",
    fontSize: jump ? "var(--fs-12)" : "var(--fs-11)",
    padding: jump ? "3px 9px" : "2px 9px",
    borderRadius: jump ? "var(--r-6)" : "var(--r-pill)",
    fontWeight: "var(--fw-medium)",
    whiteSpace: "nowrap",
    cursor: "pointer",
    border: "1px solid var(--border)",
    display: "inline-flex",
    alignItems: "center"
  };
  let skin;
  if (selected) {
    skin = {
      background: hover ? "var(--crimson-700)" : "var(--crimson-600)",
      color: "#fff",
      borderColor: "var(--crimson-600)"
    };
  } else if (hover) {
    skin = jump ? {
      background: "var(--crimson-50)",
      color: "var(--crimson-700)",
      borderColor: "var(--crimson-200)"
    } : {
      background: "var(--tint)",
      color: "var(--crimson-700)",
      borderColor: "var(--crimson-200)"
    };
  } else {
    skin = jump ? {
      background: "var(--navy-100)",
      color: "var(--navy-700)"
    } : {
      background: "var(--tint)",
      color: "var(--navy-600)"
    };
  }
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      ...base,
      ...skin,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Chip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Chip.jsx", error: String((e && e.message) || e) }); }

// components/core/Dot.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const FILL = {
  error: "var(--crimson-600)",
  advice: "var(--amber)",
  ok: "var(--green)",
  none: "var(--navy-200)"
};

/** The status marker: an 8px CSS circle. Keel draws status, never an icon for it. */
function Dot({
  tone = "none",
  size = 8,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    "aria-hidden": "true",
    style: {
      display: "inline-block",
      width: size + "px",
      height: size + "px",
      borderRadius: "var(--r-round)",
      background: FILL[tone] || FILL.none,
      verticalAlign: "middle",
      flexShrink: 0,
      ...style
    }
  }, rest));
}
Object.assign(__ds_scope, { Dot });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Dot.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** A bare Unicode glyph in a small hit area — rail collapse, card remove, disclosure. */
function IconButton({
  glyph,
  tone = "neutral",
  title,
  style,
  ...rest
}) {
  const [hover, setHover] = useState(false);
  const danger = tone === "danger";
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    title: title,
    "aria-label": title,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      border: "none",
      background: hover ? danger ? "var(--crimson-50)" : "var(--navy-100)" : "none",
      color: hover ? danger ? "var(--crimson-600)" : "var(--navy-800)" : "var(--navy-400)",
      fontFamily: "var(--font-sans)",
      fontSize: "15px",
      lineHeight: 1,
      padding: "3px 6px",
      borderRadius: "var(--r-6)",
      flexShrink: 0,
      cursor: "pointer",
      ...style
    }
  }, rest), glyph);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/data/CoverageBar.jsx
try { (() => {
/** A per-entity coverage row: mono field name, then a graded badge. */
function CoverageBar({
  label,
  percent,
  orphan,
  style
}) {
  const grade = percent >= 80 ? "ok" : percent >= 40 ? "advice" : "danger";
  const skin = orphan ? {
    bg: "var(--navy-200)",
    fg: "var(--navy-600)"
  } : grade === "ok" ? {
    bg: "var(--green-50)",
    fg: "var(--green)"
  } : grade === "advice" ? {
    bg: "var(--amber-50)",
    fg: "var(--amber)"
  } : {
    bg: "var(--crimson-50)",
    fg: "var(--crimson-700)"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "8px",
      padding: "7px 0",
      borderBottom: "1px solid var(--border2)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-13)",
      color: "var(--navy-700)",
      fontFamily: "var(--font-mono)"
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-10)",
      padding: "1px 8px",
      borderRadius: "var(--r-4)",
      fontWeight: "var(--fw-semibold)",
      whiteSpace: "nowrap",
      background: skin.bg,
      color: skin.fg,
      fontVariantNumeric: "var(--numeric)"
    }
  }, orphan ? "orphan" : percent + "%"));
}
Object.assign(__ds_scope, { CoverageBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/CoverageBar.jsx", error: String((e && e.message) || e) }); }

// components/data/DiffView.jsx
try { (() => {
/** A unified git diff in GitHub's colours, deliberately not Keel's — a reviewer reads it instantly. */
function DiffView({
  file,
  patch = "",
  loading,
  style
}) {
  const rows = [];
  let oldNo = null,
    newNo = null;
  for (const line of patch.split("\n")) {
    if (/^(diff |index |--- |\+\+\+ )/.test(line)) continue;
    const hunk = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunk) {
      oldNo = +hunk[1];
      newNo = +hunk[2];
      rows.push({
        kind: "hunk",
        text: line
      });
      continue;
    }
    if (line.startsWith("+")) rows.push({
      kind: "add",
      text: line,
      n: newNo != null ? newNo++ : ""
    });else if (line.startsWith("-")) rows.push({
      kind: "del",
      text: line,
      o: oldNo != null ? oldNo++ : ""
    });else rows.push({
      kind: "ctx",
      text: line,
      o: oldNo != null ? oldNo++ : "",
      n: newNo != null ? newNo++ : ""
    });
  }
  const SKIN = {
    add: {
      bg: "var(--diff-add-bg)",
      gutter: "var(--diff-add-gutter)",
      gfg: "var(--diff-add-gutter-fg)",
      fg: "var(--diff-add-fg)",
      accent: "var(--green)"
    },
    del: {
      bg: "var(--diff-del-bg)",
      gutter: "var(--diff-del-gutter)",
      gfg: "var(--diff-del-gutter-fg)",
      fg: "var(--diff-del-fg)",
      accent: "var(--crimson-600)"
    },
    ctx: {
      bg: "transparent",
      gutter: "var(--tint)",
      gfg: "var(--navy-400)",
      fg: "var(--navy-700)"
    },
    hunk: {
      bg: "var(--diff-hunk-bg)",
      gutter: "var(--diff-hunk-bg)",
      gfg: "var(--navy-400)",
      fg: "var(--navy-500)"
    }
  };
  if (loading) {
    return /*#__PURE__*/React.createElement("div", {
      style: {
        padding: "10px 12px",
        background: "#fff",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-8)",
        fontFamily: "var(--font-mono)",
        fontSize: "var(--fs-12)",
        color: "var(--navy-400)",
        fontStyle: "italic",
        ...style
      }
    }, "Loading diff\u2026");
  }
  const gutter = (s, val, accent) => ({
    width: "1%",
    minWidth: "42px",
    textAlign: "right",
    padding: "0 10px",
    color: s.gfg,
    background: s.gutter,
    borderRight: "1px solid var(--border2)",
    userSelect: "none",
    whiteSpace: "nowrap",
    fontVariantNumeric: "var(--numeric)",
    borderLeft: accent ? "2px solid " + accent : "none"
  });
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--border)",
      borderRadius: "var(--r-8)",
      overflow: "hidden",
      background: "#fff",
      ...style
    }
  }, file ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-11)",
      color: "var(--navy-500)",
      padding: "6px 12px",
      background: "var(--tint)",
      borderBottom: "1px solid var(--border2)",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, file) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      overflowX: "auto"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      borderCollapse: "collapse",
      width: "100%",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-12)",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("tbody", null, rows.map((r, i) => {
    const s = SKIN[r.kind];
    if (r.kind === "hunk") {
      return /*#__PURE__*/React.createElement("tr", {
        key: i,
        style: {
          background: s.bg
        }
      }, /*#__PURE__*/React.createElement("td", {
        style: {
          ...gutter(s),
          padding: "0 10px"
        }
      }), /*#__PURE__*/React.createElement("td", {
        style: {
          ...gutter(s)
        }
      }), /*#__PURE__*/React.createElement("td", {
        style: {
          padding: "0 10px",
          whiteSpace: "pre",
          color: s.fg
        }
      }, r.text));
    }
    return /*#__PURE__*/React.createElement("tr", {
      key: i,
      style: {
        background: s.bg
      }
    }, /*#__PURE__*/React.createElement("td", {
      style: gutter(s, r.o, s.accent)
    }, r.o ?? ""), /*#__PURE__*/React.createElement("td", {
      style: gutter(s)
    }, r.n ?? ""), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "0 10px",
        whiteSpace: "pre",
        color: s.fg
      }
    }, r.text));
  })))));
}
Object.assign(__ds_scope, { DiffView });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/DiffView.jsx", error: String((e && e.message) || e) }); }

// components/data/FacetPanel.jsx
try { (() => {
/** The collapsed "Filters (N)" expander in the rail. OR within a group, AND across groups. */
function FacetPanel({
  groups = [],
  selected = {},
  open,
  activeCount = 0,
  onOpen,
  onToggle,
  onClear,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderBottom: "1px solid var(--border)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => onOpen && onOpen(!open),
    style: {
      display: "flex",
      alignItems: "center",
      gap: "7px",
      padding: "8px 14px",
      cursor: "pointer",
      userSelect: "none"
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      color: "var(--navy-400)",
      fontSize: "var(--fs-10)",
      width: "10px",
      flexShrink: 0
    }
  }, open ? "▾" : "▸"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-12)",
      fontWeight: "var(--fw-semibold)",
      color: "var(--navy-700)"
    }
  }, "Filters"), activeCount ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-10)",
      fontWeight: "var(--fw-bold)",
      padding: "1px 7px",
      borderRadius: "var(--r-pill)",
      background: "var(--crimson-600)",
      color: "#fff",
      fontVariantNumeric: "var(--numeric)"
    }
  }, activeCount) : null, activeCount ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: e => {
      e.stopPropagation();
      onClear && onClear();
    },
    style: {
      marginLeft: "auto",
      border: "none",
      background: "none",
      color: "var(--navy-500)",
      fontSize: "var(--fs-11)",
      fontWeight: "var(--fw-semibold)",
      padding: "2px 4px",
      borderRadius: "var(--r-6)",
      cursor: "pointer"
    }
  }, "Clear all") : null), open ? /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "2px 14px 10px",
      maxHeight: "46vh",
      overflowY: "auto"
    }
  }, groups.map((g, gi) => /*#__PURE__*/React.createElement("div", {
    key: g.key,
    style: {
      marginTop: gi === 0 ? "4px" : "9px"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--fs-10)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-key)",
      color: "var(--navy-500)",
      fontWeight: "var(--fw-bold)",
      margin: "0 0 5px"
    }
  }, g.label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "5px"
    }
  }, g.options.map(o => {
    const v = Array.isArray(o) ? o[0] : o;
    const l = Array.isArray(o) ? o[1] : o;
    return /*#__PURE__*/React.createElement(__ds_scope.Chip, {
      key: v,
      selected: (selected[g.key] || []).includes(v),
      onClick: () => onToggle && onToggle(g.key, v)
    }, l);
  }))))) : null);
}
Object.assign(__ds_scope, { FacetPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/FacetPanel.jsx", error: String((e && e.message) || e) }); }

// components/data/GapChips.jsx
try { (() => {
/** Empty is information: unauthored fields come back as chips that jump into edit. */
function GapChips({
  label = "Gaps to review",
  items = [],
  onPick,
  dashed = true,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--section-gap)",
      borderTop: dashed ? "1px dashed var(--border)" : "none",
      paddingTop: "14px",
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: ".07em",
      color: "var(--navy-500)",
      fontWeight: "var(--fw-bold)",
      margin: "0 0 9px"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "7px"
    }
  }, items.map(it => {
    const v = Array.isArray(it) ? it[0] : it;
    const l = Array.isArray(it) ? it[1] : it;
    return /*#__PURE__*/React.createElement(__ds_scope.Chip, {
      key: v,
      variant: "jump",
      onClick: () => onPick && onPick(v)
    }, l);
  })));
}
Object.assign(__ds_scope, { GapChips });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/GapChips.jsx", error: String((e && e.message) || e) }); }

// components/data/RiskBadge.jsx
try { (() => {
/**
 * Severity escalates by WEIGHT, not by hue: only critical is a solid fill, high is
 * a wash, medium moves to amber, low goes neutral. Low is not green — green means
 * "covered", a different axis. Nothing else on a report screen may be solid crimson.
 */
const SEV = {
  critical: {
    bg: "var(--sev-critical-bg)",
    fg: "var(--sev-critical-fg)",
    line: "var(--sev-critical-line)",
    weight: "var(--fw-bold)"
  },
  high: {
    bg: "var(--sev-high-bg)",
    fg: "var(--sev-high-fg)",
    line: "var(--sev-high-line)",
    weight: "var(--fw-bold)"
  },
  medium: {
    bg: "var(--sev-medium-bg)",
    fg: "var(--sev-medium-fg)",
    line: "var(--sev-medium-line)",
    weight: "var(--fw-semibold)"
  },
  low: {
    bg: "var(--sev-low-bg)",
    fg: "var(--sev-low-fg)",
    line: "var(--sev-low-line)",
    weight: "var(--fw-medium)"
  },
  info: {
    bg: "var(--sev-info-bg)",
    fg: "var(--sev-info-fg)",
    line: "transparent",
    weight: "var(--fw-medium)"
  }
};

/**
 * The spine colour for a ranked finding card's left edge. Read it straight from the
 * tokens — `var(--sev-<level>-spine)` — so no JS map has to stay in sync:
 *   style={{ borderLeft: "4px solid var(--sev-" + f.severity + "-spine)" }}
 * Or wrap the card in <SeveritySpine level={f.severity}>.
 */
function SeveritySpine({
  level = "info",
  width = 4,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderLeft: width + "px solid var(--sev-" + level + "-spine)",
      ...style
    }
  }, children);
}
function RiskBadge({
  level = "info",
  prefix,
  style
}) {
  const s = SEV[level] || SEV.info;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "5px",
      fontSize: "var(--fs-10)",
      padding: "1px 8px",
      borderRadius: "var(--r-4)",
      fontWeight: s.weight,
      whiteSpace: "nowrap",
      textTransform: "lowercase",
      background: s.bg,
      color: s.fg,
      border: "1px solid " + s.line,
      fontFamily: "var(--font-sans)",
      ...style
    }
  }, prefix ? /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: 0.7,
      fontWeight: "var(--fw-medium)"
    }
  }, prefix) : null, level);
}
Object.assign(__ds_scope, { SeveritySpine, RiskBadge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/RiskBadge.jsx", error: String((e && e.message) || e) }); }

// components/data/SplitBar.jsx
try { (() => {
const FILL = {
  verified: "var(--green)",
  shared: "var(--green)",
  ok: "var(--green)",
  draft: "var(--amber)",
  local: "var(--amber)",
  unset: "var(--navy-200)",
  none: "var(--navy-200)"
};

/** A 10px proportional bar plus its dot legend — draft vs verified, linked vs orphaned. */
function SplitBar({
  segments = [],
  style
}) {
  const total = segments.reduce((n, s) => n + s.value, 0) || 1;
  return /*#__PURE__*/React.createElement("div", {
    style: style
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      height: "10px",
      borderRadius: "var(--r-6)",
      overflow: "hidden",
      background: "var(--navy-100)",
      margin: "8px 0 6px"
    }
  }, segments.map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      height: "100%",
      width: s.value / total * 100 + "%",
      background: FILL[s.tone] || FILL.unset
    }
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "14px",
      fontSize: "var(--fs-12)",
      color: "var(--navy-500)",
      flexWrap: "wrap"
    }
  }, segments.map((s, i) => /*#__PURE__*/React.createElement("span", {
    key: i
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      display: "inline-block",
      width: "8px",
      height: "8px",
      borderRadius: "var(--r-round)",
      marginRight: "4px",
      verticalAlign: "middle",
      background: FILL[s.tone] || FILL.unset
    }
  }), s.label, /*#__PURE__*/React.createElement("span", {
    style: {
      fontVariantNumeric: "var(--numeric)"
    }
  }, " ", s.value)))));
}
Object.assign(__ds_scope, { SplitBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/SplitBar.jsx", error: String((e && e.message) || e) }); }

// components/data/StatTile.jsx
try { (() => {
/** A dashboard count. 28px/700, tabular, tight tracking. */
function StatTile({
  value,
  label,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: "120px",
      border: "1px solid var(--border)",
      borderRadius: "var(--r-10)",
      padding: "14px 16px",
      background: "#fff",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--fs-28)",
      fontWeight: "var(--fw-bold)",
      color: "var(--navy-900)",
      letterSpacing: "var(--ls-number)",
      fontVariantNumeric: "var(--numeric)",
      lineHeight: 1.1
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--fs-12)",
      color: "var(--navy-500)",
      marginTop: "3px"
    }
  }, label));
}
Object.assign(__ds_scope, { StatTile });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/StatTile.jsx", error: String((e && e.message) || e) }); }

// components/feedback/EmptyState.jsx
try { (() => {
/** One line of navy-400 text. Keel ships no empty-state art. */
function EmptyState({
  children,
  top = "22vh",
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--navy-400)",
      marginTop: top,
      textAlign: "center",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-14)",
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { EmptyState });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/EmptyState.jsx", error: String((e && e.message) || e) }); }

// components/feedback/ErrorSummary.jsx
try { (() => {
/** Two channels, never one: red blocks the save, amber advises and never blocks. */
function ErrorSummary({
  tone = "error",
  title,
  items = [],
  style
}) {
  const err = tone === "error";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: err ? "var(--crimson-50)" : "var(--amber-50)",
      border: "1px solid " + (err ? "var(--crimson-200)" : "var(--amber)"),
      color: err ? "var(--crimson-700)" : "var(--amber)",
      borderRadius: "var(--r-8)",
      padding: "10px 14px",
      margin: "16px 0 4px",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-13)",
      lineHeight: 1.5,
      ...style
    }
  }, title ? /*#__PURE__*/React.createElement("strong", {
    style: {
      display: "block",
      marginBottom: "5px"
    }
  }, title) : null, /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      paddingLeft: "18px"
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement("li", {
    key: i
  }, it))));
}
Object.assign(__ds_scope, { ErrorSummary });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/ErrorSummary.jsx", error: String((e && e.message) || e) }); }

// components/feedback/SavedDialog.jsx
try { (() => {
/** After a write: names the file to commit. Green left accent, dismissible, stays put. */
function SavedDialog({
  file,
  message = "Written to disk.",
  show = true,
  repoUrl,
  onClose,
  style
}) {
  if (!show) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "fixed",
      bottom: "20px",
      right: "22px",
      maxWidth: "340px",
      background: "#fff",
      border: "1px solid var(--border)",
      borderLeft: "4px solid var(--green)",
      color: "var(--navy-800)",
      padding: "13px 16px",
      borderRadius: "var(--r-10)",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-13)",
      lineHeight: 1.5,
      boxShadow: "var(--shadow-dialog)",
      zIndex: 60,
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", null, message, " ", file ? /*#__PURE__*/React.createElement("code", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-12)",
      color: "var(--navy-900)"
    }
  }, file) : null), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "10px",
      display: "flex",
      gap: "12px",
      alignItems: "center"
    }
  }, repoUrl ? /*#__PURE__*/React.createElement("a", {
    href: repoUrl,
    style: {
      color: "var(--crimson-600)",
      fontWeight: "var(--fw-semibold)",
      textDecoration: "none"
    }
  }, "Open a pull request") : null, /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClose,
    style: {
      marginLeft: "auto",
      border: "none",
      background: "none",
      color: "var(--navy-400)",
      fontSize: "var(--fs-12)",
      cursor: "pointer"
    }
  }, "Dismiss")));
}
Object.assign(__ds_scope, { SavedDialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/SavedDialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
/** The bottom-right confirmation. Past tense, terse, gone in 2.2s. */
function Toast({
  message,
  tone = "neutral",
  show = true,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "fixed",
      bottom: "20px",
      right: "22px",
      background: tone === "error" ? "var(--crimson-700)" : "var(--navy-900)",
      color: "#fff",
      padding: "10px 16px",
      borderRadius: "var(--r-10)",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-13)",
      boxShadow: "var(--shadow-toast)",
      opacity: show ? 1 : 0,
      transform: show ? "translateY(0)" : "translateY(var(--toast-rise))",
      transition: "opacity var(--dur-layer), transform var(--dur-layer)",
      pointerEvents: "none",
      zIndex: 50,
      ...style
    }
  }, message);
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/WarnBanner.jsx
try { (() => {
/** An inline caveat on a read view — a dangling link, an un-gated threat. */
function WarnBanner({
  tone = "error",
  children,
  style
}) {
  const ok = tone === "ok";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: ok ? "var(--green-50)" : "var(--crimson-50)",
      border: "1px solid " + (ok ? "var(--green-200)" : "var(--crimson-200)"),
      color: ok ? "var(--green)" : "var(--crimson-700)",
      borderRadius: "var(--r-8)",
      padding: "9px 12px",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-13)",
      lineHeight: 1.5,
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { WarnBanner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/WarnBanner.jsx", error: String((e && e.message) || e) }); }

// components/forms/CheckSet.jsx
try { (() => {
const {
  useState
} = React;
function Item({
  value,
  label,
  checked,
  onToggle
}) {
  const [hover, setHover] = useState(false);
  return /*#__PURE__*/React.createElement("label", {
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
      padding: "6px 11px",
      border: "1px solid " + (hover ? "var(--crimson-200)" : "var(--navy-200)"),
      borderRadius: "var(--r-8)",
      fontSize: "var(--fs-13)",
      cursor: "pointer",
      background: "#fff",
      color: "var(--navy-800)"
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: checked,
    onChange: () => onToggle(value),
    style: {
      accentColor: "var(--crimson-600)",
      margin: 0
    }
  }), label);
}

/** Multi-value enum fields (surface, source) as a wrapping row of checkbox capsules. */
function CheckSet({
  options = [],
  value = [],
  onToggle = () => {},
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "8px",
      ...style
    }
  }, options.map(o => {
    const v = Array.isArray(o) ? o[0] : o;
    const l = Array.isArray(o) ? o[1] : o;
    return /*#__PURE__*/React.createElement(Item, {
      key: v,
      value: v,
      label: l,
      checked: value.includes(v),
      onToggle: onToggle
    });
  }));
}
Object.assign(__ds_scope, { CheckSet });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/CheckSet.jsx", error: String((e && e.message) || e) }); }

// components/forms/Field.jsx
try { (() => {
/** label + one-line hint + control + validation message. The whole form is these. */
function Field({
  label,
  hint,
  error,
  advice,
  guidance,
  reserveHint = true,
  children,
  style
}) {
  const dot = error ? "var(--crimson-600)" : advice ? "var(--amber)" : null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      minWidth: 0,
      ...style
    }
  }, label ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      fontWeight: "var(--fw-bold)",
      margin: "0 0 9px",
      display: "flex",
      alignItems: "center"
    }
  }, label, dot ? /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      display: "inline-block",
      width: "8px",
      height: "8px",
      borderRadius: "var(--r-round)",
      background: dot,
      marginLeft: "8px"
    }
  }) : null) : null, hint || reserveHint ? /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--navy-500)",
      fontSize: "var(--fs-12)",
      lineHeight: 1.4,
      margin: "0 0 6px",
      minHeight: "17px",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, hint) : null, children, error ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--fs-12)",
      marginTop: "5px",
      lineHeight: 1.4,
      color: "var(--crimson-700)"
    }
  }, error) : null, !error && advice ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--fs-12)",
      marginTop: "5px",
      lineHeight: 1.4,
      color: "var(--amber)"
    }
  }, advice) : null, guidance ? /*#__PURE__*/React.createElement("details", {
    style: {
      marginTop: "8px"
    }
  }, /*#__PURE__*/React.createElement("summary", {
    style: {
      listStyle: "none",
      cursor: "pointer",
      display: "inline-flex",
      alignItems: "center",
      gap: "5px",
      fontSize: "var(--fs-11)",
      fontWeight: "var(--fw-semibold)",
      color: "var(--navy-500)",
      padding: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      color: "var(--navy-400)",
      fontSize: "13px"
    }
  }, "\u24D8"), "How to write this"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "6px",
      padding: "10px 12px",
      background: "#fff",
      border: "1px solid var(--navy-200)",
      borderRadius: "var(--r-8)",
      fontSize: "var(--fs-12)",
      color: "var(--navy-600)",
      lineHeight: 1.5
    }
  }, guidance)) : null);
}
Object.assign(__ds_scope, { Field });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Field.jsx", error: String((e && e.message) || e) }); }

// components/forms/SearchInput.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** The rail filter field: tint fill that goes white on focus, 9px radius. */
function SearchInput({
  style,
  ...rest
}) {
  const [focus, setFocus] = useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "10px 14px",
      borderBottom: "1px solid var(--border)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "search",
    autoComplete: "off",
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: "100%",
      padding: "9px 11px",
      background: focus ? "#fff" : "var(--tint)",
      color: "var(--navy-900)",
      border: "1px solid " + (focus ? "var(--crimson-600)" : "var(--border)"),
      borderRadius: "var(--r-9)",
      outline: "none",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-13)"
    }
  }, rest)));
}
Object.assign(__ds_scope, { SearchInput });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/SearchInput.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** A fixed-vocabulary dropdown. Options always come from the JSON Schema, never hardcoded. */
function Select({
  invalid,
  options = [],
  placeholder,
  style,
  ...rest
}) {
  const [focus, setFocus] = useState(false);
  return /*#__PURE__*/React.createElement("select", _extends({
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: "100%",
      minHeight: "var(--input-h)",
      border: "1px solid var(--navy-200)",
      borderRadius: "var(--r-8)",
      padding: "8px 10px",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-14)",
      lineHeight: "var(--lh-base)",
      color: "var(--navy-900)",
      background: "#fff",
      outline: "none",
      borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
      boxShadow: focus ? "var(--focus-ring)" : "none",
      ...style
    }
  }, rest), placeholder ? /*#__PURE__*/React.createElement("option", {
    value: ""
  }, placeholder) : null, options.map(o => {
    const value = Array.isArray(o) ? o[0] : o;
    const label = Array.isArray(o) ? o[1] : o;
    return /*#__PURE__*/React.createElement("option", {
      key: value,
      value: value
    }, label);
  }));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextArea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** The multi-line prose control — weakness text, reachability, rationale. */
function TextArea({
  invalid,
  rows = 4,
  style,
  ...rest
}) {
  const [focus, setFocus] = useState(false);
  return /*#__PURE__*/React.createElement("textarea", _extends({
    rows: rows,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: "100%",
      border: "1px solid var(--navy-200)",
      borderRadius: "var(--r-8)",
      padding: "8px 10px",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--fs-14)",
      lineHeight: "var(--lh-base)",
      color: "var(--navy-900)",
      background: "#fff",
      outline: "none",
      resize: "vertical",
      borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
      boxShadow: focus ? "var(--focus-ring)" : "none",
      ...style
    }
  }, rest));
}
Object.assign(__ds_scope, { TextArea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextArea.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextInput.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState
} = React;
/** The single-line text control. 38px min-height, crimson focus ring. */
function TextInput({
  invalid,
  mono,
  title,
  style,
  ...rest
}) {
  const [focus, setFocus] = useState(false);
  return /*#__PURE__*/React.createElement("input", _extends({
    type: "text",
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: "100%",
      minHeight: "var(--input-h)",
      border: "1px solid var(--navy-200)",
      borderRadius: "var(--r-8)",
      padding: "8px 10px",
      fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
      fontSize: title ? "var(--fs-19)" : "var(--fs-14)",
      fontWeight: title ? "var(--fw-bold)" : "var(--fw-regular)",
      lineHeight: "var(--lh-base)",
      color: "var(--navy-900)",
      background: "#fff",
      outline: "none",
      borderColor: focus ? "var(--crimson-600)" : invalid ? "var(--crimson-200)" : "var(--navy-200)",
      boxShadow: focus ? "var(--focus-ring)" : "none",
      ...style
    }
  }, rest));
}
Object.assign(__ds_scope, { TextInput });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextInput.jsx", error: String((e && e.message) || e) }); }

// components/structure/Breadcrumb.jsx
try { (() => {
const {
  useState
} = React;
function Crumb({
  children,
  onClick
}) {
  const [h, setH] = useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClick,
    onMouseEnter: () => setH(true),
    onMouseLeave: () => setH(false),
    style: {
      border: "none",
      background: "none",
      padding: 0,
      font: "inherit",
      fontWeight: "var(--fw-semibold)",
      cursor: "pointer",
      color: h ? "var(--crimson-600)" : "var(--navy-500)",
      textDecoration: h ? "underline" : "none"
    }
  }, children);
}

/** The quiet type/id line above a read view, plus its optional provenance line. */
function Breadcrumb({
  type,
  id,
  onType,
  lastChanged,
  onViewChange,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: style
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "6px",
      fontSize: "var(--fs-12)",
      color: "var(--navy-400)",
      marginBottom: "12px"
    }
  }, /*#__PURE__*/React.createElement(Crumb, {
    onClick: onType
  }, type), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--navy-400)"
    }
  }, "/"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--navy-500)"
    }
  }, id)), lastChanged ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--fs-12)",
      color: "var(--navy-400)",
      margin: "-4px 0 12px"
    }
  }, lastChanged, onViewChange ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onViewChange,
    style: {
      border: "none",
      background: "none",
      color: "var(--crimson-600)",
      fontWeight: "var(--fw-semibold)",
      fontSize: "var(--fs-12)",
      padding: "0 0 0 4px",
      cursor: "pointer"
    }
  }, "view change") : null) : null);
}
Object.assign(__ds_scope, { Breadcrumb });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/Breadcrumb.jsx", error: String((e && e.message) || e) }); }

// components/structure/Card.jsx
try { (() => {
const {
  useState
} = React;
/** A white card on a tint band — a weakness, a mitigation link, a report finding. */
function Card({
  id,
  title,
  rationale,
  desc,
  badges,
  jump,
  onClick,
  children,
  style
}) {
  const [hover, setHover] = useState(false);
  const interactive = Boolean(jump || onClick);
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      border: "1px solid " + (interactive && hover ? "var(--crimson-200)" : "var(--border)"),
      background: interactive && hover ? "var(--crimson-50)" : "#fff",
      borderRadius: "var(--r-10)",
      padding: "var(--pad-card)",
      marginBottom: "10px",
      cursor: interactive ? "pointer" : "default",
      transition: "background var(--dur-hover), border-color var(--dur-hover)",
      ...style
    }
  }, id || title || badges ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      flexWrap: "wrap"
    }
  }, id ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-11)",
      color: "var(--navy-400)"
    }
  }, id) : null, title ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--fw-semibold)",
      color: "var(--navy-900)",
      fontSize: "var(--fs-14)"
    }
  }, title) : null, badges) : null, desc ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "6px 0 0",
      color: "var(--navy-600)",
      fontSize: "var(--fs-13)",
      whiteSpace: "pre-wrap",
      lineHeight: 1.5
    }
  }, desc) : null, rationale ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "7px 0 0",
      color: "var(--navy-500)",
      fontSize: "var(--fs-13)",
      fontStyle: "italic",
      whiteSpace: "pre-wrap",
      lineHeight: 1.5
    }
  }, rationale) : null, children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/Card.jsx", error: String((e && e.message) || e) }); }

// components/structure/EditorCard.jsx
try { (() => {
/** A collapsible repeatable form record. Its border is the only heavy container in a form. */
function EditorCard({
  summary,
  open = true,
  hasError,
  onToggle,
  onRemove,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      border: "1px solid " + (hasError && !open ? "var(--crimson-200)" : "var(--border)"),
      borderRadius: "var(--r-10)",
      marginBottom: "10px",
      background: "var(--tint)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: onToggle,
    style: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: open ? "10px 12px" : "9px 12px",
      cursor: "pointer",
      userSelect: "none"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    glyph: open ? "▾" : "▸",
    title: open ? "Collapse" : "Expand",
    style: {
      fontSize: "11px",
      padding: "2px 3px"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      minWidth: 0,
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
      fontSize: "var(--fs-13)",
      color: "var(--navy-700)",
      fontWeight: "var(--fw-semibold)",
      fontFamily: "var(--font-mono)"
    }
  }, summary), hasError && !open ? /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      display: "inline-block",
      width: "8px",
      height: "8px",
      borderRadius: "var(--r-round)",
      background: "var(--crimson-600)",
      flexShrink: 0
    }
  }) : null, onRemove ? /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    glyph: "\xD7",
    tone: "danger",
    title: "Remove",
    onClick: e => {
      e.stopPropagation();
      onRemove();
    }
  }) : null), open ? /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "2px 14px 14px"
    }
  }, children) : null);
}
Object.assign(__ds_scope, { EditorCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/EditorCard.jsx", error: String((e && e.message) || e) }); }

// components/structure/EntityHeader.jsx
try { (() => {
/** The detail-page header: letter tile, title, mono id, badges, actions. */
function EntityHeader({
  glyph,
  title,
  id,
  badges,
  actions,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: "14px",
      paddingBottom: "20px",
      marginBottom: "4px",
      borderBottom: "1px solid var(--border)",
      ...style
    }
  }, glyph ? /*#__PURE__*/React.createElement("div", {
    style: {
      width: "42px",
      height: "42px",
      borderRadius: "var(--r-10)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#fff",
      flexShrink: 0,
      fontSize: "20px",
      fontWeight: "var(--fw-bold)",
      background: "var(--crimson-600)"
    }
  }, glyph) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: "var(--fs-20)",
      fontWeight: "var(--fw-bold)",
      letterSpacing: "var(--ls-title)",
      color: "var(--navy-900)"
    }
  }, title), id ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--navy-400)",
      fontSize: "var(--fs-12)",
      marginTop: "4px"
    }
  }, id) : null, badges ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "5px",
      flexWrap: "wrap",
      marginTop: "8px"
    }
  }, badges) : null), actions ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "8px",
      flexShrink: 0
    }
  }, actions) : null);
}
Object.assign(__ds_scope, { EntityHeader });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/EntityHeader.jsx", error: String((e && e.message) || e) }); }

// components/structure/RailRow.jsx
try { (() => {
const {
  useState
} = React;
/** A list row in the left rail. Selected = crimson wash + a 3px inset crimson accent. */
function RailRow({
  id,
  title,
  badges,
  selected,
  onClick,
  style
}) {
  const [hover, setHover] = useState(false);
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      padding: "var(--pad-rail-row)",
      borderBottom: "1px solid var(--border2)",
      display: "flex",
      flexDirection: "column",
      gap: "2px",
      cursor: "pointer",
      background: selected ? "var(--crimson-50)" : hover ? "var(--navy-100)" : "transparent",
      boxShadow: selected ? "var(--selected-rail-accent)" : "none",
      ...style
    }
  }, id ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-11)",
      color: "var(--navy-500)",
      fontFamily: "var(--font-mono)",
      letterSpacing: ".01em"
    }
  }, id) : null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-14)",
      color: "var(--navy-900)",
      fontWeight: "var(--fw-medium)",
      lineHeight: "var(--lh-tight)"
    }
  }, title), badges ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "5px",
      flexWrap: "wrap",
      marginTop: "3px"
    }
  }, badges) : null);
}
Object.assign(__ds_scope, { RailRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/RailRow.jsx", error: String((e && e.message) || e) }); }

// components/structure/ScreenTabs.jsx
try { (() => {
/** The rail's top screen switcher. Inert tint strip; the active tab is white with a crimson underline. */
function ScreenTabs({
  screens = [],
  value,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("nav", {
    style: {
      display: "flex",
      ...style
    }
  }, screens.map(s => {
    const v = Array.isArray(s) ? s[0] : s;
    const l = Array.isArray(s) ? s[1] : s;
    const on = v === value;
    return /*#__PURE__*/React.createElement("button", {
      key: v,
      type: "button",
      onClick: () => onChange && onChange(v),
      style: {
        flex: 1,
        border: "none",
        cursor: "pointer",
        background: on ? "var(--panel)" : "var(--tint)",
        color: on ? "var(--navy-900)" : "var(--navy-500)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--fs-12)",
        fontWeight: "var(--fw-semibold)",
        padding: "10px 8px",
        borderBottom: "2px solid " + (on ? "var(--crimson-600)" : "var(--border)")
      }
    }, l);
  }));
}
Object.assign(__ds_scope, { ScreenTabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/ScreenTabs.jsx", error: String((e && e.message) || e) }); }

// components/structure/SectionBand.jsx
try { (() => {
/**
 * The band that carries a section. Read view and edit form wear the SAME surface,
 * so toggling Edit never makes the eye lose its place — that is review-first in CSS.
 */
function SectionBand({
  label,
  sub,
  as = "section",
  count,
  children,
  style
}) {
  const isForm = as === "fieldset";
  const Tag = isForm ? "fieldset" : "section";
  const LabelTag = isForm ? "legend" : "h3";
  return /*#__PURE__*/React.createElement(Tag, {
    style: {
      background: "var(--tint)",
      border: "1px solid var(--border2)",
      borderRadius: "var(--r-10)",
      padding: "var(--pad-section)",
      margin: isForm ? "14px 0 0" : 0,
      marginTop: "14px",
      minWidth: 0,
      ...style
    }
  }, label ? /*#__PURE__*/React.createElement(LabelTag, {
    style: {
      display: "block",
      width: "100%",
      float: "none",
      padding: 0,
      margin: "0 0 9px",
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      fontWeight: "var(--fw-bold)"
    }
  }, label, sub ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--fw-regular)",
      textTransform: "none",
      color: "var(--navy-400)"
    }
  }, " ", sub) : null, count != null ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--navy-400)",
      fontSize: "var(--fs-11)",
      fontWeight: "var(--fw-medium)",
      textTransform: "none",
      letterSpacing: 0,
      marginLeft: "8px"
    }
  }, count) : null) : null, children);
}
Object.assign(__ds_scope, { SectionBand });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/structure/SectionBand.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/MitigationsScreen.jsx
try { (() => {
const {
  RailRow,
  SearchInput,
  FacetPanel,
  SectionBand,
  Card,
  EntityHeader,
  Breadcrumb,
  Button,
  Badge,
  GapChips,
  DiffView,
  EmptyState,
  WarnBanner
} = window.KeelDesignSystem_7d5998;
const MIT_PATCH = `@@ -6,6 +6,8 @@ purpose: Restrict the agent to the smallest set of tools
 failure_behavior: 'Fail closed: an unlisted tool call is refused and logged.'
-implementations: []
+implementations:
+- name: Gateway tool policy
+  owner: Platform Security`;
function MitigationsRail({
  data,
  sel,
  onSelect,
  q,
  setQ,
  facets,
  setFacets,
  open,
  setOpen,
  collapsed,
  setCollapsed,
  onNew
}) {
  const E = data.enums;
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.mitigations.filter(m => {
    if (q && ![m.id, m.name, m.purpose].join(" ").toLowerCase().includes(q.toLowerCase())) return false;
    if (facets.mitigation_class.length && !facets.mitigation_class.includes(m.mitigation_class)) return false;
    if (facets.status.length && !facets.status.includes(m.status)) return false;
    if (facets.implementations.length) {
      const v = m.implementations.length ? "recorded" : "empty";
      if (!facets.implementations.includes(v)) return false;
    }
    return true;
  });
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(RailHeader, {
    title: "Keel \xB7 Mitigations",
    count: items.length + " / " + data.mitigations.length,
    onNew: onNew,
    collapsed: collapsed,
    onCollapse: () => setCollapsed(c => !c)
  }), collapsed ? null : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SearchInput, {
    placeholder: "Filter mitigations\u2026",
    value: q,
    onChange: e => setQ(e.target.value)
  }), /*#__PURE__*/React.createElement(FacetPanel, {
    open: open,
    onOpen: setOpen,
    activeCount: active,
    selected: facets,
    onClear: () => setFacets({
      mitigation_class: [],
      status: [],
      implementations: []
    }),
    onToggle: (k, v) => setFacets(f => ({
      ...f,
      [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v]
    })),
    groups: [{
      key: "mitigation_class",
      label: "Class",
      options: E.mitigation_class
    }, {
      key: "status",
      label: "Status",
      options: E.status
    }, {
      key: "implementations",
      label: "Implementations",
      options: [["recorded", "recorded"], ["empty", "ships empty"]]
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: "auto",
      flex: 1,
      minHeight: 0
    }
  }, items.length ? items.map(m => /*#__PURE__*/React.createElement(RailRow, {
    key: m.id,
    id: m.id,
    title: m.name,
    selected: sel === m.id,
    onClick: () => onSelect(m.id),
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
      tone: "soft",
      mono: true
    }, m.mitigation_class), /*#__PURE__*/React.createElement(Badge, {
      tone: m.status === "verified" ? "ok" : "advice"
    }, m.status))
  })) : /*#__PURE__*/React.createElement(EmptyState, {
    top: "40px"
  }, "No matches."))));
}
function MitigationRead({
  m,
  threats,
  onEdit,
  onDelete,
  onJump,
  onGap,
  showDiff,
  setShowDiff
}) {
  const gaps = [];
  if (!m.implementations.length) gaps.push("implementations");
  if (!m.failure_behavior) gaps.push("failure_behavior");
  const linked = threats.filter(t => t.mitigations.some(l => l.id === m.id));
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Breadcrumb, {
    type: "Mitigations",
    id: m.id,
    lastChanged: "Last changed 6 days ago by jane",
    onViewChange: () => setShowDiff(d => !d)
  }), showDiff ? /*#__PURE__*/React.createElement(DiffView, {
    file: "catalog/mitigations/" + m.id + ".yaml",
    patch: MIT_PATCH,
    style: {
      marginBottom: "14px"
    }
  }) : null, /*#__PURE__*/React.createElement(EntityHeader, {
    glyph: "C",
    title: m.name,
    id: m.id,
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
      tone: "type",
      mono: true
    }, m.mitigation_class), /*#__PURE__*/React.createElement(Badge, {
      tone: m.status === "verified" ? "ok" : "advice"
    }, m.status), /*#__PURE__*/React.createElement(Badge, {
      tone: "soft"
    }, linked.length, " threats addressed")),
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      onClick: onDelete
    }, "Delete"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      onClick: onEdit
    }, "Edit"))
  }), m.mitigation_class === "detector" ? /*#__PURE__*/React.createElement(WarnBanner, {
    style: {
      marginTop: "16px"
    }
  }, "A detector fails open. It lowers likelihood and never closes the path \u2014 link it as soft.") : null, /*#__PURE__*/React.createElement(SectionBand, {
    label: "Purpose"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, m.purpose)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Scope"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, m.scope)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Control mechanism"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, m.control_mechanism)), m.failure_behavior ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "Failure behavior"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, m.failure_behavior)) : null, m.implementations.length ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "Implementations",
    sub: "how this org realizes the control",
    count: m.implementations.length
  }, m.implementations.map((im, i) => /*#__PURE__*/React.createElement(Card, {
    key: i,
    title: im.name,
    badges: /*#__PURE__*/React.createElement(Badge, {
      tone: "soft"
    }, im.owner),
    desc: im.note,
    style: i === m.implementations.length - 1 ? {
      marginBottom: 0
    } : null
  }))) : null, /*#__PURE__*/React.createElement(SectionBand, {
    label: "Addresses",
    count: linked.length
  }, linked.length ? linked.map((t, i) => {
    const link = t.mitigations.find(l => l.id === m.id);
    return /*#__PURE__*/React.createElement(Card, {
      key: t.id,
      id: t.id,
      title: t.title,
      jump: true,
      onClick: () => onJump(t.id),
      badges: /*#__PURE__*/React.createElement(Badge, {
        tone: link.strength === "gating" ? "harm" : "soft"
      }, link.strength),
      rationale: link.rationale,
      style: i === linked.length - 1 ? {
        marginBottom: 0
      } : null
    });
  }) : /*#__PURE__*/React.createElement(Prose, null, "Nothing links to this card yet.")), gaps.length ? /*#__PURE__*/React.createElement(GapChips, {
    items: gaps,
    onPick: onGap
  }) : null);
}
Object.assign(window, {
  MitigationsRail,
  MitigationRead
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/MitigationsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/OverviewScreen.jsx
try { (() => {
const {
  StatTile,
  CoverageBar,
  SplitBar,
  GapChips,
  WarnBanner,
  Badge
} = window.KeelDesignSystem_7d5998;
function OverviewScreen({
  data,
  onJump
}) {
  const s = data.stats,
    cov = data.coverage;
  // Both halves come from stats, not from the 6-row sample in data.mitigations.
  const verified = s.verified;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "12px",
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement(StatTile, {
    value: s.threats,
    label: "threats"
  }), /*#__PURE__*/React.createElement(StatTile, {
    value: s.mitigations,
    label: "mitigations"
  }), /*#__PURE__*/React.createElement(StatTile, {
    value: s.links,
    label: "mitigation links"
  }), /*#__PURE__*/React.createElement(StatTile, {
    value: s.systems,
    label: "systems assessed"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "16px",
      alignItems: "start",
      marginTop: "16px"
    }
  }, /*#__PURE__*/React.createElement(PanelCard, {
    label: "Style-guide coverage"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: "10px",
      marginBottom: "10px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-24)",
      fontWeight: "var(--fw-bold)",
      letterSpacing: "var(--ls-number)",
      fontVariantNumeric: "var(--numeric)"
    }
  }, cov.overall, "%"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-12)",
      color: "var(--text-muted)"
    }
  }, "of model fields carry authoring guidance")), cov.entities.map(e => /*#__PURE__*/React.createElement(CoverageBar, {
    key: e.entity,
    label: e.entity,
    percent: e.overall
  })), cov.entities[0].fields.map(f => /*#__PURE__*/React.createElement(CoverageBar, {
    key: f.name,
    label: f.name,
    percent: f.pct,
    orphan: f.orphan
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "16px"
    }
  }, /*#__PURE__*/React.createElement(PanelCard, {
    label: "Mitigation status"
  }, /*#__PURE__*/React.createElement(SplitBar, {
    segments: [{
      tone: "verified",
      label: "verified",
      value: verified
    }, {
      tone: "draft",
      label: "draft",
      value: s.mitigations - verified
    }]
  }), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      margin: "16px 0 0",
      fontWeight: "var(--fw-bold)"
    }
  }, "Implementations recorded"), /*#__PURE__*/React.createElement(SplitBar, {
    segments: [{
      tone: "ok",
      label: "recorded",
      value: s.implementations_recorded
    }, {
      tone: "unset",
      label: "empty",
      value: s.mitigations - s.implementations_recorded
    }]
  })), /*#__PURE__*/React.createElement(PanelCard, {
    label: "Recent activity"
  }, data.activity.map((a, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: "8px",
      padding: "7px 0",
      borderBottom: i === data.activity.length - 1 ? "none" : "1px solid var(--line-inner)",
      fontSize: "var(--fs-13)",
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-body-read)"
    }
  }, a.msg), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      fontFamily: "var(--font-mono)"
    }
  }, a.meta)))))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "16px"
    }
  }, /*#__PURE__*/React.createElement(PanelCard, {
    label: "Gaps to review"
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      margin: "0 0 12px"
    }
  }, "Nothing here blocks anything. It is a place to see where the model is thin."), data.gaps.map(g => /*#__PURE__*/React.createElement("div", {
    key: g.name,
    style: {
      marginBottom: "10px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "8px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--fw-semibold)",
      color: "var(--text-body-read)",
      fontSize: "var(--fs-14)"
    }
  }, g.name), /*#__PURE__*/React.createElement(Badge, {
    tone: "danger",
    numeric: true
  }, g.ids.length)), /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      margin: "4px 0 0"
    }
  }, g.desc), /*#__PURE__*/React.createElement(GapChips, {
    label: "",
    items: g.ids.map(i => [i.split(" ::")[0], i]),
    onPick: onJump,
    dashed: false,
    style: {
      marginTop: "4px"
    }
  }))))));
}
Object.assign(window, {
  OverviewScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/OverviewScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/ReportsScreen.jsx
try { (() => {
const {
  RailRow,
  SearchInput,
  SectionBand,
  Card,
  EntityHeader,
  Breadcrumb,
  Button,
  Badge,
  RiskBadge,
  EmptyState,
  WarnBanner
} = window.KeelDesignSystem_7d5998;
const RANK = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3
};
function ReportsRail({
  data,
  sel,
  onSelect,
  q,
  setQ,
  collapsed,
  setCollapsed
}) {
  const items = data.reports.filter(r => !q || r.system_name.toLowerCase().includes(q.toLowerCase()));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(RailHeader, {
    title: "Keel \xB7 Reports",
    count: items.length + " / " + data.reports.length,
    collapsed: collapsed,
    onCollapse: () => setCollapsed(c => !c)
  }), collapsed ? null : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SearchInput, {
    placeholder: "Filter systems\u2026",
    value: q,
    onChange: e => setQ(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: "auto",
      flex: 1,
      minHeight: 0
    }
  }, items.length ? items.map(r => /*#__PURE__*/React.createElement(RailRow, {
    key: r.system_id,
    id: r.system_id,
    title: r.system_name,
    selected: sel === r.system_id,
    onClick: () => onSelect(r.system_id),
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, r.top_severity ? /*#__PURE__*/React.createElement(RiskBadge, {
      level: r.top_severity
    }) : null, /*#__PURE__*/React.createElement(Badge, {
      tone: "soft",
      numeric: true
    }, r.latest_date), /*#__PURE__*/React.createElement(Badge, {
      tone: "soft",
      numeric: true
    }, r.report_count, " runs"))
  })) : /*#__PURE__*/React.createElement(EmptyState, {
    top: "40px"
  }, "No matches."))));
}
function Finding({
  f,
  rank
}) {
  const [open, setOpen] = React.useState(rank === 0);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--line-panel)",
      borderLeft: "4px solid var(--sev-" + f.severity + "-spine)",
      borderRadius: "var(--r-10)",
      background: "var(--surface-panel)",
      marginBottom: "10px",
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => setOpen(o => !o),
    style: {
      display: "flex",
      alignItems: "center",
      gap: "10px",
      padding: "12px 15px",
      cursor: "pointer",
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      color: "var(--text-faint)",
      fontSize: "var(--fs-10)",
      width: "10px",
      flexShrink: 0
    }
  }, open ? "▾" : "▸"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-12)",
      fontFamily: "var(--font-mono)",
      color: "var(--text-faint)",
      minWidth: "22px",
      flexShrink: 0,
      fontVariantNumeric: "var(--numeric)"
    }
  }, rank + 1, "."), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-12)",
      color: "var(--text-muted)",
      whiteSpace: "nowrap",
      flexShrink: 0
    }
  }, f.id), /*#__PURE__*/React.createElement(RiskBadge, {
    level: f.severity,
    prefix: "severity"
  }), /*#__PURE__*/React.createElement(RiskBadge, {
    level: f.likelihood,
    prefix: "likelihood"
  }), /*#__PURE__*/React.createElement(Badge, {
    tone: "type",
    mono: true
  }, f.harm), /*#__PURE__*/React.createElement(Badge, {
    tone: "soft"
  }, "complexity ", f.complexity)), open ? /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 15px 14px"
    }
  }, /*#__PURE__*/React.createElement(SectionBand, {
    label: "Scenario",
    style: {
      marginTop: 0
    }
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, f.scenario)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Source"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "auto 1fr",
      gap: "4px 14px",
      fontSize: "var(--fs-13)"
    }
  }, [["who", f.source.who], ["motive", f.source.motive], ["access", f.source.access], ["asset", f.asset], ["attack surface", f.attack_surface]].map(([k, v]) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: k
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-meta)",
      color: "var(--text-faint)",
      paddingTop: "3px"
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-body-read)"
    }
  }, v))))), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Vulnerability"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, f.vulnerability)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Risk",
    sub: f.severity + " · " + f.likelihood
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, f.reasoning)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Requirements",
    count: f.requirements.length
  }, f.requirements.map((r, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      marginTop: i ? "7px" : 0
    }
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: "8px",
      cursor: "pointer",
      fontSize: "var(--fs-13)",
      color: "var(--text-body)"
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    defaultChecked: r.status === "already_covered",
    style: {
      margin: "3px 0 0",
      flexShrink: 0,
      accentColor: "var(--accent)"
    }
  }), /*#__PURE__*/React.createElement("span", null, r.id ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--fs-12)",
      color: "var(--text-body-read)"
    }
  }, r.id) : /*#__PURE__*/React.createElement("span", null, r.description, " ", /*#__PURE__*/React.createElement(Badge, {
    tone: "advice"
  }, "ad hoc")), r.id ? /*#__PURE__*/React.createElement(Badge, {
    tone: r.status === "already_covered" ? "ok" : "advice",
    style: {
      marginLeft: "8px"
    }
  }, r.status) : null)), r.note ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "3px 0 0 24px",
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      fontStyle: "italic",
      lineHeight: 1.5
    }
  }, r.note) : null)), f.ignored.length ? f.ignored.map(ig => /*#__PURE__*/React.createElement("p", {
    key: ig.id,
    style: {
      marginTop: "9px",
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      fontStyle: "italic",
      lineHeight: 1.5
    }
  }, "Ignored \u2014 ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontStyle: "normal"
    }
  }, ig.id), ": ", ig.reason)) : null), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Delta",
    sub: "against the previous run"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, f.delta))) : null);
}
function ReportScreen({
  report,
  onJump
}) {
  const ranked = [...report.findings].sort((a, b) => RANK[a.severity] - RANK[b.severity]);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Breadcrumb, {
    type: "Reports",
    id: report.system_id + " / " + report.date
  }), /*#__PURE__*/React.createElement(EntityHeader, {
    glyph: "R",
    title: report.system_name,
    id: report.system_id + " · " + report.date,
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
      tone: "soft"
    }, report.assessor.split(" <")[0]), /*#__PURE__*/React.createElement(RiskBadge, {
      level: ranked.length ? ranked[0].severity : "info",
      prefix: ranked.filter(f => RANK[f.severity] <= 1).length + " at"
    }), /*#__PURE__*/React.createElement(Badge, {
      tone: "soft",
      numeric: true
    }, report.findings.length, " findings"), /*#__PURE__*/React.createElement(Badge, {
      tone: "soft",
      numeric: true
    }, report.discarded.length, " discarded")),
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      size: "sm"
    }, "Export YAML"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm"
    }, "New assessment"))
  }), /*#__PURE__*/React.createElement(SectionBand, {
    label: "System"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, report.system_description)), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Delta summary",
    sub: "what changed since the last run"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, report.delta_summary)), /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      margin: "24px 0 9px",
      fontWeight: "var(--fw-bold)"
    }
  }, "Findings ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--fw-regular)",
      textTransform: "none",
      color: "var(--text-faint)"
    }
  }, "ranked by severity")), ranked.map((f, i) => /*#__PURE__*/React.createElement(Finding, {
    key: f.id,
    f: f,
    rank: i
  })), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Discarded",
    sub: "ruled out on reachability, judged un-mitigated",
    count: report.discarded.length
  }, report.discarded.map((d, i) => /*#__PURE__*/React.createElement(Card, {
    key: d.id,
    id: d.id,
    jump: true,
    onClick: () => onJump(d.id),
    desc: d.reason,
    style: i === report.discarded.length - 1 ? {
      marginBottom: 0
    } : null
  }))), /*#__PURE__*/React.createElement(SectionBand, {
    label: "Assessor dialogue",
    sub: "the questions that set the grades",
    count: report.dialogue.length
  }, report.dialogue.map((d, i) => /*#__PURE__*/React.createElement(Card, {
    key: i,
    style: i === report.dialogue.length - 1 ? {
      marginBottom: 0
    } : null
  }, [["Q", d.q], ["A", d.a], ["→", d.impact]].map(([k, v]) => /*#__PURE__*/React.createElement("p", {
    key: k,
    style: {
      marginTop: k === "Q" ? 0 : "5px",
      marginBottom: 0,
      fontSize: "var(--fs-13)",
      color: k === "→" ? "var(--text-muted)" : "var(--text-body)",
      lineHeight: 1.55
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      minWidth: "18px",
      fontWeight: "var(--fw-bold)",
      color: "var(--text-muted)"
    }
  }, k), v))))));
}
Object.assign(window, {
  ReportsRail,
  ReportScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/ReportsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/StyleGuideScreen.jsx
try { (() => {
const {
  RailRow,
  SearchInput,
  FacetPanel,
  SectionBand,
  EntityHeader,
  Button,
  Badge,
  Field,
  TextInput,
  TextArea,
  EmptyState,
  CoverageBar,
  IconButton
} = window.KeelDesignSystem_7d5998;
function StyleRail({
  data,
  sel,
  onSelect,
  q,
  setQ,
  facets,
  setFacets,
  open,
  setOpen,
  collapsed,
  setCollapsed
}) {
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.styleFields.filter(f => {
    if (q && !(f.entity + "." + f.field).toLowerCase().includes(q.toLowerCase())) return false;
    if (facets.entity.length && !facets.entity.includes(f.entity)) return false;
    if (facets.orphan.length && !facets.orphan.includes(f.orphan ? "orphan" : "linked")) return false;
    return true;
  });
  const byEntity = {};
  items.forEach(f => {
    (byEntity[f.entity] = byEntity[f.entity] || []).push(f);
  });
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(RailHeader, {
    title: "Keel \xB7 Style guide",
    count: items.length + " / " + data.styleFields.length,
    collapsed: collapsed,
    onCollapse: () => setCollapsed(c => !c)
  }), collapsed ? null : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SearchInput, {
    placeholder: "Filter fields\u2026",
    value: q,
    onChange: e => setQ(e.target.value)
  }), /*#__PURE__*/React.createElement(FacetPanel, {
    open: open,
    onOpen: setOpen,
    activeCount: active,
    selected: facets,
    onClear: () => setFacets({
      entity: [],
      orphan: []
    }),
    onToggle: (k, v) => setFacets(f => ({
      ...f,
      [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v]
    })),
    groups: [{
      key: "entity",
      label: "Entity",
      options: ["threat", "mitigation"]
    }, {
      key: "orphan",
      label: "Model field",
      options: [["linked", "matches the model"], ["orphan", "orphan"]]
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: "auto",
      flex: 1,
      minHeight: 0
    }
  }, items.length ? Object.entries(byEntity).map(([ent, fields]) => /*#__PURE__*/React.createElement("div", {
    key: ent
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "9px 15px 5px",
      fontSize: "var(--fs-10)",
      textTransform: "uppercase",
      letterSpacing: ".07em",
      color: "var(--text-muted)",
      fontWeight: "var(--fw-bold)",
      background: "var(--surface-inset)",
      borderTop: "1px solid var(--line-inner)",
      borderBottom: "1px solid var(--line-inner)"
    }
  }, ent), fields.map(f => {
    const on = sel === ent + "." + f.field;
    const tone = f.orphan ? "orphan" : f.pct >= 80 ? "ok" : f.pct >= 40 ? "advice" : "danger";
    return /*#__PURE__*/React.createElement("div", {
      key: f.field,
      onClick: () => onSelect(ent + "." + f.field),
      style: {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "8px",
        padding: "var(--pad-rail-row)",
        borderBottom: "1px solid var(--line-inner)",
        cursor: "pointer",
        background: on ? "var(--surface-selected)" : "transparent",
        boxShadow: on ? "var(--selected-rail-accent)" : "none"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: "var(--fs-13)",
        color: "var(--text-body-read)",
        fontFamily: "var(--font-mono)"
      }
    }, f.field), /*#__PURE__*/React.createElement(Badge, {
      tone: tone,
      numeric: true
    }, f.orphan ? "orphan" : f.pct + "%"));
  }))) : /*#__PURE__*/React.createElement(EmptyState, {
    top: "40px"
  }, "No matches."))));
}
const DEFAULT_SLOTS = {
  purpose: "",
  include: [],
  avoid: [],
  example: ""
};
function StyleEditor({
  field,
  onSave
}) {
  const [slots, setSlots] = React.useState(field.slots || DEFAULT_SLOTS);
  React.useEffect(() => setSlots(field.slots || DEFAULT_SLOTS), [field.entity, field.field]);
  const list = (key, label, hint) => /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: label,
    count: (slots[key] || []).length
  }, /*#__PURE__*/React.createElement(Field, {
    label: "",
    hint: hint
  }, /*#__PURE__*/React.createElement("ul", {
    style: {
      listStyle: "none",
      margin: "6px 0 0",
      padding: 0
    }
  }, (slots[key] || []).map((v, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      display: "flex",
      gap: "8px",
      alignItems: "center",
      marginBottom: "7px"
    }
  }, /*#__PURE__*/React.createElement(TextInput, {
    value: v,
    onChange: e => setSlots(s => ({
      ...s,
      [key]: s[key].map((x, j) => j === i ? e.target.value : x)
    }))
  }), /*#__PURE__*/React.createElement(IconButton, {
    glyph: "\xD7",
    tone: "danger",
    title: "Remove slot",
    onClick: () => setSlots(s => ({
      ...s,
      [key]: s[key].filter((_, j) => j !== i)
    }))
  })))), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    glyph: "\uFF0B",
    onClick: () => setSlots(s => ({
      ...s,
      [key]: [...(s[key] || []), ""]
    }))
  }, "Add slot")));
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(EntityHeader, {
    glyph: "S",
    title: field.field,
    id: field.entity + "." + field.field,
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, field.orphan ? /*#__PURE__*/React.createElement(Badge, {
      tone: "orphan"
    }, "orphan \u2014 no matching model field") : /*#__PURE__*/React.createElement(Badge, {
      tone: field.pct >= 80 ? "ok" : field.pct >= 40 ? "advice" : "danger",
      numeric: true
    }, field.pct, "% covered")),
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      onClick: () => onSave(field)
    }, "Save")
  }), /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: "Purpose"
  }, /*#__PURE__*/React.createElement(Field, {
    label: "",
    hint: "One sentence an author reads before they write the field."
  }, /*#__PURE__*/React.createElement(TextArea, {
    rows: 2,
    value: slots.purpose,
    onChange: e => setSlots(s => ({
      ...s,
      purpose: e.target.value
    }))
  }))), list("include", "What to include", "One line each. These become the bullets in the author's guidance panel."), list("avoid", "What to avoid", "Name the specific failure, not a generality."), /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: "Example"
  }, /*#__PURE__*/React.createElement(Field, {
    label: "",
    hint: "A real line from the catalog an author can drop in and adapt."
  }, /*#__PURE__*/React.createElement(TextArea, {
    rows: 2,
    value: slots.example,
    onChange: e => setSlots(s => ({
      ...s,
      example: e.target.value
    }))
  }))));
}

/** The right rail earns its column here: exactly what an author sees while you edit. */
function StylePreview({
  field
}) {
  const s = field.slots;
  if (!s) return /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-faint)",
      fontSize: "var(--fs-13)",
      fontStyle: "italic"
    }
  }, "No guidance authored for this field yet.");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--line-panel)",
      borderRadius: "var(--r-10)",
      padding: "14px 15px",
      background: "var(--surface-inset)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      fontWeight: "var(--fw-bold)",
      marginBottom: "9px"
    }
  }, field.field), /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-muted)",
      fontSize: "var(--fs-12)",
      lineHeight: 1.4,
      margin: "0 0 6px"
    }
  }, s.purpose), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#fff",
      border: "1px solid var(--line-control)",
      borderRadius: "var(--r-8)",
      padding: "10px 12px",
      fontSize: "var(--fs-12)"
    }
  }, [["What to include", s.include], ["What to avoid", s.avoid]].map(([k, arr]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      marginBottom: "8px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: "var(--fw-bold)",
      textTransform: "uppercase",
      letterSpacing: var_ls,
      fontSize: "var(--fs-10)",
      color: "var(--navy-600)",
      marginBottom: "3px"
    }
  }, k), /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      paddingLeft: "16px",
      color: "var(--text-body)"
    }
  }, arr.map((x, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      marginBottom: "2px"
    }
  }, x))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: "var(--fw-bold)",
      textTransform: "uppercase",
      letterSpacing: var_ls,
      fontSize: "var(--fs-10)",
      color: "var(--navy-600)",
      marginBottom: "3px"
    }
  }, "Example"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-body-read)",
      fontStyle: "italic",
      margin: 0
    }
  }, s.example))));
}
const var_ls = ".05em";
Object.assign(window, {
  StyleRail,
  StyleEditor,
  StylePreview
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/StyleGuideScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/ThreatsScreen.jsx
try { (() => {
const {
  RailRow,
  SearchInput,
  FacetPanel,
  SectionBand,
  Card,
  EditorCard,
  EntityHeader,
  Breadcrumb,
  Button,
  Badge,
  Field,
  TextInput,
  TextArea,
  Select,
  CheckSet,
  GapChips,
  DiffView,
  ErrorSummary,
  WarnBanner,
  EmptyState
} = window.KeelDesignSystem_7d5998;
const PATCH = `@@ -18,7 +18,9 @@ weaknesses:
   nature: targeted
-reachability: NOT applicable if the tool is read-only.
+reachability: NOT applicable if the reachable tools have no operations with real
+  consequences (read-only, no side effects), or the model influences neither the
+  choice of tool nor its arguments (a rigidly predefined pipeline).
 mitigations:
 - id: CTRL-TOOL-ALLOWLIST`;
function ThreatsRail({
  data,
  sel,
  onSelect,
  q,
  setQ,
  facets,
  setFacets,
  open,
  setOpen,
  collapsed,
  setCollapsed,
  onNew
}) {
  const E = data.enums;
  const active = Object.values(facets).reduce((n, a) => n + a.length, 0);
  const items = data.threats.filter(t => {
    const hay = [t.id, t.title, t.reachability, ...t.weaknesses.map(w => w.text)].join(" ").toLowerCase();
    if (q && !hay.includes(q.toLowerCase())) return false;
    for (const [k, vals] of Object.entries(facets)) {
      if (!vals.length) continue;
      const mine = k === "harm" ? [t.harm] : k === "component" ? t.weaknesses.map(w => w.component) : k === "mitigation" ? t.mitigations.length ? t.mitigations.some(m => m.strength === "gating") ? ["gating"] : ["soft"] : ["none"] : t[k] || [];
      if (!mine.some(v => vals.includes(v))) return false;
    }
    return true;
  });
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(RailHeader, {
    title: "Keel \xB7 Threats",
    count: items.length + " / " + data.threats.length,
    onNew: onNew,
    collapsed: collapsed,
    onCollapse: () => setCollapsed(c => !c)
  }), collapsed ? null : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SearchInput, {
    placeholder: "Filter threats\u2026",
    value: q,
    onChange: e => setQ(e.target.value)
  }), /*#__PURE__*/React.createElement(FacetPanel, {
    open: open,
    onOpen: setOpen,
    activeCount: active,
    selected: facets,
    onClear: () => setFacets({
      harm: [],
      surface: [],
      source: [],
      component: [],
      mitigation: []
    }),
    onToggle: (k, v) => setFacets(f => ({
      ...f,
      [k]: f[k].includes(v) ? f[k].filter(x => x !== v) : [...f[k], v]
    })),
    groups: [{
      key: "harm",
      label: "Harm",
      options: E.harm
    }, {
      key: "surface",
      label: "Surface",
      options: E.surface
    }, {
      key: "source",
      label: "Source",
      options: E.source
    }, {
      key: "component",
      label: "Weakness component",
      options: E.component
    }, {
      key: "mitigation",
      label: "Mitigation strength",
      options: [["gating", "has a gating control"], ["soft", "soft only"], ["none", "none linked"]]
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: "auto",
      flex: 1,
      minHeight: 0
    }
  }, items.length ? items.map(t => /*#__PURE__*/React.createElement(RailRow, {
    key: t.id,
    id: t.id,
    title: t.title,
    selected: sel === t.id,
    onClick: () => onSelect(t.id),
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
      tone: "type",
      mono: true
    }, t.harm), t.mitigations.length ? null : /*#__PURE__*/React.createElement(Badge, {
      tone: "advice"
    }, "no mitigation"), t.weaknesses.length ? null : /*#__PURE__*/React.createElement(Badge, {
      tone: "advice"
    }, "no weakness"))
  })) : /*#__PURE__*/React.createElement(EmptyState, {
    top: "40px"
  }, "No matches."))));
}
function ThreatRead({
  t,
  mitById,
  onEdit,
  onDelete,
  onJump,
  onGap,
  showDiff,
  setShowDiff
}) {
  const gaps = [];
  if (!t.reachability) gaps.push("reachability");
  if (!t.references.length) gaps.push("references");
  if (!t.tags.length) gaps.push("tags");
  if (!t.weaknesses.length) gaps.push("weaknesses");
  if (!t.mitigations.length) gaps.push("mitigations");
  const gating = t.mitigations.filter(m => m.strength === "gating").length;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Breadcrumb, {
    type: "Threats",
    id: t.id,
    lastChanged: t.lastChanged,
    onViewChange: () => setShowDiff(d => !d)
  }), showDiff ? /*#__PURE__*/React.createElement(DiffView, {
    file: "catalog/threats/" + t.id + ".yaml",
    patch: PATCH,
    style: {
      marginBottom: "14px"
    }
  }) : null, /*#__PURE__*/React.createElement(EntityHeader, {
    glyph: "T",
    title: t.title,
    id: t.id,
    badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
      tone: "type",
      mono: true
    }, t.harm), t.surface.map(s => /*#__PURE__*/React.createElement(Badge, {
      key: s,
      tone: "soft"
    }, s)), t.source.map(s => /*#__PURE__*/React.createElement(Badge, {
      key: s,
      tone: "soft"
    }, s)), t.tags.map(s => /*#__PURE__*/React.createElement(Badge, {
      key: s,
      tone: "ok"
    }, s))),
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      onClick: onDelete
    }, "Delete"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      onClick: onEdit
    }, "Edit"))
  }), t.mitigations.length && !gating ? /*#__PURE__*/React.createElement(WarnBanner, {
    style: {
      marginTop: "16px"
    }
  }, "Every mitigation on this threat is soft \u2014 nothing gates it.") : null, t.weaknesses.length ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "Weaknesses",
    sub: "the predisposing conditions it rests on",
    count: t.weaknesses.length
  }, t.weaknesses.map((w, i) => /*#__PURE__*/React.createElement(Card, {
    key: i,
    id: w.component,
    badges: /*#__PURE__*/React.createElement(Badge, {
      tone: w.nature === "targeted" ? "type" : "soft"
    }, w.nature),
    desc: w.text,
    style: i === t.weaknesses.length - 1 ? {
      marginBottom: 0
    } : null
  }))) : null, t.reachability ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "Reachability",
    sub: "when it is NOT a live path, judged un-mitigated"
  }, /*#__PURE__*/React.createElement(Prose, {
    read: true
  }, t.reachability)) : null, t.mitigations.length ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "Mitigations",
    count: gating + " gating · " + (t.mitigations.length - gating) + " soft"
  }, t.mitigations.map((m, i) => {
    const card = mitById[m.id];
    return /*#__PURE__*/React.createElement(Card, {
      key: m.id,
      id: m.id,
      title: card ? card.name : "— card not found —",
      jump: true,
      onClick: () => onJump(m.id),
      badges: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Badge, {
        tone: m.strength === "gating" ? "harm" : "soft"
      }, m.strength), card ? null : /*#__PURE__*/React.createElement(Badge, {
        tone: "danger"
      }, "dangling")),
      rationale: m.rationale,
      style: i === t.mitigations.length - 1 ? {
        marginBottom: 0
      } : null
    });
  })) : null, t.references.length ? /*#__PURE__*/React.createElement(SectionBand, {
    label: "References"
  }, t.references.map(r => /*#__PURE__*/React.createElement(Card, {
    key: r.id,
    id: r.id,
    desc: r.url,
    style: {
      marginBottom: 0
    }
  }))) : null, gaps.length ? /*#__PURE__*/React.createElement(GapChips, {
    items: gaps,
    onPick: onGap
  }) : /*#__PURE__*/React.createElement("p", {
    style: {
      color: "var(--text-faint)",
      fontSize: "var(--fs-12)",
      fontStyle: "italic",
      margin: "16px 0 0"
    }
  }, "Every field on this threat is authored."));
}
function ThreatEdit({
  t,
  enums,
  focusField,
  onCancel,
  onSave
}) {
  const [draft, setDraft] = React.useState(t);
  const [openCards, setOpenCards] = React.useState([0]);
  React.useEffect(() => setDraft(t), [t.id]);
  const set = (k, v) => setDraft(d => ({
    ...d,
    [k]: v
  }));
  const errors = draft.title.trim() ? [] : ["title: a threat must have a title"];
  const advice = [];
  if (!draft.weaknesses.length) advice.push("weaknesses: a threat should rest on at least one architectural condition");
  if (draft.mitigations.length && !draft.mitigations.some(m => m.strength === "gating")) advice.push("mitigations: every link is soft — nothing gates this threat");
  if (!draft.reachability) advice.push("reachability: no carve-out authored, so every deployment inherits this threat");
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(EntityHeader, {
    glyph: "T",
    title: "Editing",
    id: draft.id,
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      onClick: onCancel
    }, "Cancel"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      disabled: errors.length > 0,
      onClick: () => onSave(draft)
    }, "Save"))
  }), errors.length ? /*#__PURE__*/React.createElement(ErrorSummary, {
    title: errors.length + " problems block this save",
    items: errors
  }) : null, advice.length ? /*#__PURE__*/React.createElement(ErrorSummary, {
    tone: "advice",
    title: advice.length + " things worth a look",
    items: advice
  }) : null, /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: "Identity"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "var(--field-gap)"
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Title",
    hint: "One line: the action plus its consequence.",
    error: errors.length ? "Required." : null
  }, /*#__PURE__*/React.createElement(TextInput, {
    title: true,
    value: draft.title,
    invalid: errors.length > 0,
    autoFocus: focusField === "title",
    onChange: e => set("title", e.target.value)
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Harm",
    hint: "The consequence class if it fires."
  }, /*#__PURE__*/React.createElement(Select, {
    value: draft.harm,
    options: enums.harm,
    onChange: e => set("harm", e.target.value)
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Surface",
    hint: "Which trust boundary untrusted influence crosses."
  }, /*#__PURE__*/React.createElement(CheckSet, {
    options: enums.surface,
    value: draft.surface,
    onToggle: v => set("surface", draft.surface.includes(v) ? draft.surface.filter(x => x !== v) : [...draft.surface, v])
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Source",
    hint: "Who or what drives it."
  }, /*#__PURE__*/React.createElement(CheckSet, {
    options: enums.source,
    value: draft.source,
    onToggle: v => set("source", draft.source.includes(v) ? draft.source.filter(x => x !== v) : [...draft.source, v])
  })))), /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: "Weaknesses",
    count: draft.weaknesses.length
  }, draft.weaknesses.map((w, i) => /*#__PURE__*/React.createElement(EditorCard, {
    key: i,
    summary: w.component + " · " + w.nature,
    open: openCards.includes(i),
    onToggle: () => setOpenCards(o => o.includes(i) ? o.filter(x => x !== i) : [...o, i]),
    onRemove: () => set("weaknesses", draft.weaknesses.filter((_, j) => j !== i))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "var(--field-gap)"
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Component",
    hint: "Which owned part it sits on."
  }, /*#__PURE__*/React.createElement(Select, {
    value: w.component,
    options: enums.component,
    onChange: e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? {
      ...x,
      component: e.target.value
    } : x))
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Nature",
    hint: "targeted exploits it; secondary only amplifies."
  }, /*#__PURE__*/React.createElement(Select, {
    value: w.nature,
    options: enums.nature,
    onChange: e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? {
      ...x,
      nature: e.target.value
    } : x))
  }))), /*#__PURE__*/React.createElement(Field, {
    label: "Text",
    hint: "Cause + where + defect \u2014 an architectural condition, not a narrative.",
    guidance: "State the condition that predisposes the system. Do not describe an attacker's steps, and do not name a control.",
    style: {
      marginTop: "var(--field-gap)"
    }
  }, /*#__PURE__*/React.createElement(TextArea, {
    rows: 3,
    value: w.text,
    onChange: e => set("weaknesses", draft.weaknesses.map((x, j) => j === i ? {
      ...x,
      text: e.target.value
    } : x))
  })))), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    glyph: "\uFF0B",
    onClick: () => set("weaknesses", [...draft.weaknesses, {
      component: "tool",
      nature: "targeted",
      text: ""
    }])
  }, "Add weakness")), /*#__PURE__*/React.createElement(SectionBand, {
    as: "fieldset",
    label: "Reachability",
    sub: "the rule-out gate"
  }, /*#__PURE__*/React.createElement(Field, {
    label: "",
    hint: "Open with \u201CNOT applicable if\u201D. Judge on the un-mitigated architecture.",
    reserveHint: true,
    advice: draft.reachability ? null : "No carve-out authored yet.",
    guidance: "Describe the architecture that removes the path \u2014 never a control that mitigates it. Two carve-outs at most."
  }, /*#__PURE__*/React.createElement(TextArea, {
    rows: 3,
    value: draft.reachability,
    autoFocus: focusField === "reachability",
    onChange: e => set("reachability", e.target.value),
    placeholder: "NOT applicable if\u2026"
  }))));
}
Object.assign(window, {
  ThreatsRail,
  ThreatRead,
  ThreatEdit
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/ThreatsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/app.jsx
try { (() => {
const {
  EmptyState,
  Prose: _unused
} = window.KeelDesignSystem_7d5998;
const DATA = window.KEEL_DATA;
const mitById = Object.fromEntries(DATA.mitigations.map(m => [m.id, m]));
function App() {
  const [screen, setScreen] = React.useState("overview");
  const [toast, setToast] = React.useState(null);
  const [saved, setSaved] = React.useState(null);

  // Threats
  const [tSel, setTSel] = React.useState("T-TOOL-ABUSE");
  const [tQ, setTQ] = React.useState("");
  const [tFacets, setTFacets] = React.useState({
    harm: [],
    surface: [],
    source: [],
    component: [],
    mitigation: []
  });
  const [tFacetsOpen, setTFacetsOpen] = React.useState(false);
  const [editing, setEditing] = React.useState(false);
  const [focusField, setFocusField] = React.useState(null);
  const [tDiff, setTDiff] = React.useState(false);
  const [threats, setThreats] = React.useState(DATA.threats);

  // Mitigations
  const [mSel, setMSel] = React.useState("CTRL-TOOL-ALLOWLIST");
  const [mQ, setMQ] = React.useState("");
  const [mFacets, setMFacets] = React.useState({
    mitigation_class: [],
    status: [],
    implementations: []
  });
  const [mFacetsOpen, setMFacetsOpen] = React.useState(false);
  const [mDiff, setMDiff] = React.useState(false);

  // Style guide
  const [sSel, setSSel] = React.useState("threat.reachability");
  const [sQ, setSQ] = React.useState("");
  const [sFacets, setSFacets] = React.useState({
    entity: [],
    orphan: []
  });
  const [sFacetsOpen, setSFacetsOpen] = React.useState(false);

  // Reports
  const [rSel, setRSel] = React.useState("checkout-agent");
  const [rQ, setRQ] = React.useState("");
  const flash = (message, tone) => {
    setToast({
      message,
      tone
    });
    setTimeout(() => setToast(null), 2200);
  };
  const data = {
    ...DATA,
    threats
  };
  const threat = threats.find(t => t.id === tSel);
  const mit = DATA.mitigations.find(m => m.id === mSel);
  const styleField = DATA.styleFields.find(f => f.entity + "." + f.field === sSel);
  const jumpToThreat = id => {
    const t = threats.find(x => x.id === id);
    if (t) {
      setTSel(id);
      setEditing(false);
      setTDiff(false);
      setScreen("threats");
    } else flash("That threat is not in the catalog.", "error");
  };
  const jumpToMit = id => {
    if (mitById[id]) {
      setMSel(id);
      setMDiff(false);
      setScreen("mitigations");
    } else flash("That mitigation card no longer exists.", "error");
  };
  const railFor = ({
    collapsed,
    setCollapsed
  }) => {
    if (screen === "overview") return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(RailHeader, {
      title: "Keel \xB7 Overview",
      count: "",
      collapsed: collapsed,
      onCollapse: () => setCollapsed(c => !c)
    }), collapsed ? null : /*#__PURE__*/React.createElement("div", {
      style: {
        padding: "16px 15px",
        color: "var(--navy-500)",
        fontSize: "var(--fs-13)",
        lineHeight: "var(--lh-legend)"
      }
    }, "A snapshot of the library \u2014 counts, style-guide coverage, and soft gaps worth a look. Nothing here blocks a save."));
    if (screen === "threats") return /*#__PURE__*/React.createElement(ThreatsRail, {
      data: data,
      sel: tSel,
      onSelect: id => {
        setTSel(id);
        setEditing(false);
        setTDiff(false);
      },
      q: tQ,
      setQ: setTQ,
      facets: tFacets,
      setFacets: setTFacets,
      open: tFacetsOpen,
      setOpen: setTFacetsOpen,
      collapsed: collapsed,
      setCollapsed: setCollapsed,
      onNew: () => flash("Draft threat created.")
    });
    if (screen === "mitigations") return /*#__PURE__*/React.createElement(MitigationsRail, {
      data: data,
      sel: mSel,
      onSelect: id => {
        setMSel(id);
        setMDiff(false);
      },
      q: mQ,
      setQ: setMQ,
      facets: mFacets,
      setFacets: setMFacets,
      open: mFacetsOpen,
      setOpen: setMFacetsOpen,
      collapsed: collapsed,
      setCollapsed: setCollapsed,
      onNew: () => flash("Draft mitigation card created.")
    });
    if (screen === "style") return /*#__PURE__*/React.createElement(StyleRail, {
      data: data,
      sel: sSel,
      onSelect: setSSel,
      q: sQ,
      setQ: setSQ,
      facets: sFacets,
      setFacets: setSFacets,
      open: sFacetsOpen,
      setOpen: setSFacetsOpen,
      collapsed: collapsed,
      setCollapsed: setCollapsed
    });
    return /*#__PURE__*/React.createElement(ReportsRail, {
      data: data,
      sel: rSel,
      onSelect: setRSel,
      q: rQ,
      setQ: setRQ,
      collapsed: collapsed,
      setCollapsed: setCollapsed
    });
  };
  let main = null;
  if (screen === "overview") main = /*#__PURE__*/React.createElement(OverviewScreen, {
    data: data,
    onJump: id => id.startsWith("CTRL") ? jumpToMit(id) : jumpToThreat(id)
  });else if (screen === "threats") main = !threat ? /*#__PURE__*/React.createElement(EmptyState, null, "Select a threat from the list.") : editing ? /*#__PURE__*/React.createElement(ThreatEdit, {
    t: threat,
    enums: DATA.enums,
    focusField: focusField,
    onCancel: () => {
      setEditing(false);
      setFocusField(null);
    },
    onSave: d => {
      setThreats(ts => ts.map(x => x.id === d.id ? d : x));
      setEditing(false);
      setFocusField(null);
      setSaved({
        file: "catalog/threats/" + d.id + ".yaml"
      });
    }
  }) : /*#__PURE__*/React.createElement(ThreatRead, {
    t: threat,
    mitById: mitById,
    onJump: jumpToMit,
    onEdit: () => setEditing(true),
    onDelete: () => flash("Delete needs a confirmation step.", "error"),
    onGap: f => {
      setFocusField(f);
      setEditing(true);
    },
    showDiff: tDiff,
    setShowDiff: setTDiff
  });else if (screen === "mitigations") main = !mit ? /*#__PURE__*/React.createElement(EmptyState, null, "Select a mitigation card from the list.") : /*#__PURE__*/React.createElement(MitigationRead, {
    m: mit,
    threats: threats,
    onJump: jumpToThreat,
    onEdit: () => flash("Mitigation editing lives on the same form as threats."),
    onDelete: () => flash("Deleting a card unlinks it from every threat.", "error"),
    onGap: () => flash("Jumped to the first unauthored field."),
    showDiff: mDiff,
    setShowDiff: setMDiff
  });else if (screen === "style") main = !styleField ? /*#__PURE__*/React.createElement(EmptyState, null, "Select a field from the tree.") : /*#__PURE__*/React.createElement(StyleEditor, {
    field: styleField,
    onSave: f => setSaved({
      file: "catalog/style_guide/" + f.entity + ".yaml"
    })
  });else main = /*#__PURE__*/React.createElement(ReportScreen, {
    report: DATA.report,
    onJump: jumpToThreat
  });
  const preview = screen === "style" && styleField ? /*#__PURE__*/React.createElement(StylePreview, {
    field: styleField
  }) : null;
  return /*#__PURE__*/React.createElement(AppShell, {
    screen: screen,
    onScreen: s => {
      setScreen(s);
      setEditing(false);
    },
    rail: railFor,
    main: main,
    preview: preview,
    previewTitle: "What the author sees",
    toast: toast,
    saved: saved,
    onCloseSaved: () => setSaved(null)
  });
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/app.jsx", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/data.js
try { (() => {
// Fake but faithful slices of the real catalog (keel/catalog/*.yaml) and reports/.
window.KEEL_DATA = {
  enums: {
    harm: ["wrong-decision", "data-exposed", "code-execution", "downtime", "reputation-legal"],
    surface: ["user-agent", "agent-agent", "agent-environment"],
    source: ["external-attacker", "internal", "hallucination", "error", "accident", "training-data"],
    component: ["model", "tool", "downstream", "memory", "knowledge-base", "identity-store"],
    nature: ["targeted", "secondary"],
    strength: ["gating", "soft"],
    mitigation_class: ["gating_control", "detector", "process", "evidential_mitigation", "corrective"],
    status: ["draft", "verified"]
  },
  stats: {
    threats: 13,
    mitigations: 71,
    links: 96,
    systems: 2,
    verified: 44,
    implementations_recorded: 9
  },
  coverage: {
    overall: 68,
    entities: [{
      entity: "threat",
      overall: 74,
      fields: [{
        name: "threat.weaknesses",
        pct: 100
      }, {
        name: "threat.harm",
        pct: 100
      }, {
        name: "threat.reachability",
        pct: 62
      }, {
        name: "threat.references",
        pct: 15
      }, {
        name: "threat.mitre_id",
        pct: 0,
        orphan: true
      }]
    }, {
      entity: "mitigation",
      overall: 61,
      fields: [{
        name: "mitigation.purpose",
        pct: 100
      }, {
        name: "mitigation.control_mechanism",
        pct: 88
      }, {
        name: "mitigation.failure_behavior",
        pct: 54
      }, {
        name: "mitigation.implementations",
        pct: 13
      }]
    }]
  },
  gaps: [{
    name: "Threats with no mitigation",
    desc: "Nothing addresses these yet — a floor, not a failure.",
    ids: ["T-METADATA-LEAK", "T-TOXIC"]
  }, {
    name: "Threats missing a weakness",
    desc: "A threat must rest on at least one architectural condition.",
    ids: ["T-SHADOW-AI"]
  }, {
    name: "Dangling mitigation links",
    desc: "The link points at a card that no longer exists.",
    ids: ["T-DOS :: CTRL-LEGACY-GUARD"]
  }],
  activity: [{
    msg: "Add threat: tool description poisoning",
    meta: "jane · 2 days ago · 4f2a9c1"
  }, {
    msg: "Tighten reachability on T-TOOL-ABUSE",
    meta: "sam · 3 days ago · 91be03d"
  }, {
    msg: "Record implementation for CTRL-HUMAN-IN-LOOP",
    meta: "jane · 6 days ago · 27dd14a"
  }],
  threats: [{
    id: "T-TOOL-ABUSE",
    title: "Unauthorized or destructive tool action",
    harm: "code-execution",
    surface: ["agent-environment", "user-agent"],
    source: ["external-attacker", "hallucination"],
    tags: [],
    reachability: "NOT applicable if the reachable tools have no operations with real consequences (read-only, no side effects), or the model influences neither the choice of tool nor its arguments (a rigidly predefined pipeline).",
    weaknesses: [{
      component: "tool",
      nature: "targeted",
      text: "A reachable tool performs destructive/irreversible or privileged operations (delete, admin, exec, persistent side effects), and the call is initiated by the model with no out-of-model authorization on the action itself."
    }, {
      component: "tool",
      nature: "targeted",
      text: "Arguments or the choice of action are formed by the model and hijacked via injection or agent goal substitution; the tool performs an action the user did not request."
    }, {
      component: "tool",
      nature: "targeted",
      text: "A tool with terminal/shell access is invoked on the model's initiative — a direct path to RCE."
    }, {
      component: "tool",
      nature: "targeted",
      text: "The confirmation mechanism (HITL) is not risk-differentiated and is devalued by a stream of identical requests: a critical action is approved mechanically."
    }],
    mitigations: [{
      id: "CTRL-TOOL-ALLOWLIST",
      strength: "gating",
      rationale: "An allowlist of permitted tools limits exposure of destructive operations to only those tools the agent actually needs"
    }, {
      id: "CTRL-IRREVERSIBLE-ACTION-GUARD",
      strength: "gating",
      rationale: "A guard against irreversible actions requires additional confirmation and logging"
    }, {
      id: "CTRL-HACT-CRITICAL",
      strength: "gating",
      rationale: "Mandatory human confirmation for critical tools ensures that fatigue does not lead to critical actions being missed"
    }, {
      id: "CTRL-INPUT-FILTERING",
      strength: "soft",
      rationale: "Filtering input for prompt injection"
    }, {
      id: "CTRL-PROMPT-HARDENING",
      strength: "soft",
      rationale: "Hardening the system prompt separates instructions from external content"
    }],
    references: [],
    lastChanged: "Last changed 3 days ago by sam"
  }, {
    id: "T-DATA-LEAK",
    title: "Sensitive data leaves through the agent",
    harm: "data-exposed",
    surface: ["user-agent"],
    source: ["external-attacker", "hallucination"],
    tags: ["pii"],
    reachability: "NOT applicable if the agent has no read path to data the requesting principal is not already entitled to.",
    weaknesses: [{
      component: "downstream",
      nature: "targeted",
      text: "A retrieval tool carries a broad service token, so scoping depends entirely on the token rather than on the requesting principal."
    }, {
      component: "memory",
      nature: "secondary",
      text: "Conversation memory persists across principals, so data from one session can be surfaced in another."
    }],
    mitigations: [{
      id: "CTRL-DATA-ACCESS-CONTROL",
      strength: "gating",
      rationale: "Per-principal scoping at the data layer stops a broad token from widening the read path"
    }, {
      id: "CTRL-DLP",
      strength: "soft",
      rationale: "Egress inspection catches known-shape secrets after the fact"
    }],
    references: [{
      id: "LLM02",
      url: "https://owasp.org/www-project-top-10-for-large-language-model-applications/"
    }],
    lastChanged: "Last changed 9 days ago by jane"
  }, {
    id: "T-CMD-INJECT",
    title: "Command injection through a tool",
    harm: "code-execution",
    surface: ["agent-environment"],
    source: ["external-attacker"],
    tags: [],
    reachability: "NOT applicable if no tool reaches an interpreter, a shell, or a code-execution runtime.",
    weaknesses: [{
      component: "tool",
      nature: "targeted",
      text: "A tool concatenates model output into a shell or interpreter invocation rather than passing parameterized arguments."
    }],
    mitigations: [{
      id: "CTRL-COMMAND-SANDBOX",
      strength: "gating",
      rationale: "A command allowlist restricts the tool's executable actions"
    }, {
      id: "CTRL-INPUT-PARAMETERIZATION",
      strength: "gating",
      rationale: "Parameterized calls instead of string concatenation prevent injection"
    }],
    references: [],
    lastChanged: "Last changed 3 weeks ago by sam"
  }, {
    id: "T-METADATA-LEAK",
    title: "Metadata discloses more than the answer",
    harm: "data-exposed",
    surface: ["user-agent"],
    source: ["error"],
    tags: [],
    reachability: "",
    weaknesses: [{
      component: "model",
      nature: "secondary",
      text: "Tool-call traces and citations are returned verbatim, exposing internal identifiers and paths."
    }],
    mitigations: [],
    references: [],
    lastChanged: "Last changed 5 weeks ago by jane"
  }, {
    id: "T-SSRF",
    title: "Agent-driven request forgery",
    harm: "data-exposed",
    surface: ["agent-environment"],
    source: ["external-attacker"],
    tags: [],
    reachability: "NOT applicable if no tool accepts a URL or host derived from model output.",
    weaknesses: [{
      component: "tool",
      nature: "targeted",
      text: "A fetch tool takes its target host from model output with no allowlist, so internal endpoints are reachable."
    }],
    mitigations: [{
      id: "CTRL-URL-ALLOWLIST",
      strength: "gating",
      rationale: "An egress allowlist prevents the agent reaching internal endpoints"
    }],
    references: [],
    lastChanged: "Last changed 4 days ago by sam"
  }, {
    id: "T-DOS",
    title: "Resource exhaustion through the agent loop",
    harm: "downtime",
    surface: ["user-agent"],
    source: ["external-attacker", "accident"],
    tags: [],
    reachability: "NOT applicable if the agent runs bounded, pre-paid work with a hard iteration cap.",
    weaknesses: [{
      component: "model",
      nature: "targeted",
      text: "The agent loop has no iteration or token ceiling, so one request can consume unbounded compute."
    }],
    mitigations: [{
      id: "CTRL-ITERATION-LIMITS",
      strength: "gating",
      rationale: "A hard iteration ceiling bounds the loop"
    }, {
      id: "CTRL-LEGACY-GUARD",
      strength: "soft",
      rationale: "Legacy throttle (card removed from the catalog)"
    }],
    references: [],
    lastChanged: "Last changed 2 months ago by jane"
  }, {
    id: "T-SHADOW-AI",
    title: "Unsanctioned model or tool in the path",
    harm: "reputation-legal",
    surface: ["agent-environment"],
    source: ["internal"],
    tags: ["governance"],
    reachability: "",
    weaknesses: [],
    mitigations: [{
      id: "CTRL-SHADOW-AI-POLICY",
      strength: "soft",
      rationale: "Policy plus discovery narrows unsanctioned use"
    }],
    references: [],
    lastChanged: "Last changed 6 weeks ago by sam"
  }],
  mitigations: [{
    id: "CTRL-TOOL-ALLOWLIST",
    name: "Tool allowlist",
    mitigation_class: "gating_control",
    status: "verified",
    purpose: "Restrict the agent to the smallest set of tools its task actually needs, so destructive operations are not reachable at all.",
    scope: "Every agent runtime that resolves a tool registry at session start.",
    control_mechanism: "The runtime resolves tool names against a static per-agent allowlist before dispatch. A name outside the list is refused without reaching the tool layer.",
    failure_behavior: "Fail closed: an unlisted tool call is refused and logged as a policy event.",
    implementations: [{
      name: "Gateway tool policy",
      owner: "Platform Security",
      note: "Allowlist lives in the agent manifest, enforced at the gateway."
    }],
    addresses: ["T-TOOL-ABUSE", "T-CMD-INJECT"]
  }, {
    id: "CTRL-HACT-CRITICAL",
    name: "Human confirmation for critical actions",
    mitigation_class: "process",
    status: "verified",
    purpose: "Put a person in front of any action whose consequences cannot be undone.",
    scope: "Tools classified critical: money movement, deletion, privilege change.",
    control_mechanism: "The runtime blocks on an explicit approval for any tool tagged critical, showing the resolved arguments rather than the model's intent.",
    failure_behavior: "Fail closed: no approval, no call.",
    implementations: [],
    addresses: ["T-TOOL-ABUSE"]
  }, {
    id: "CTRL-IRREVERSIBLE-ACTION-GUARD",
    name: "Irreversible action guard",
    mitigation_class: "gating_control",
    status: "draft",
    purpose: "Require a second, out-of-model signal before an action that cannot be reversed.",
    scope: "Any tool with persistent external side effects.",
    control_mechanism: "A guard evaluates the resolved call against an irreversibility classifier and demands a second factor — a ticket, a countersignature, or a delay window.",
    failure_behavior: "Fail closed.",
    implementations: [],
    addresses: ["T-TOOL-ABUSE"]
  }, {
    id: "CTRL-DATA-ACCESS-CONTROL",
    name: "Per-principal data access control",
    mitigation_class: "gating_control",
    status: "verified",
    purpose: "Scope every read to the principal who asked, not to the service the tool runs as.",
    scope: "All retrieval and lookup tools.",
    control_mechanism: "The gateway mints a per-session token carrying the end principal; downstream services authorize against that token only.",
    failure_behavior: "Fail closed: an out-of-scope lookup returns 403 before it reaches the service.",
    implementations: [{
      name: "Session-scoped gateway tokens",
      owner: "Platform Security",
      note: "Rolled out to all storefront agents."
    }],
    addresses: ["T-DATA-LEAK"]
  }, {
    id: "CTRL-INPUT-FILTERING",
    name: "Input filtering",
    mitigation_class: "detector",
    status: "draft",
    purpose: "Detect known injection and jailbreak shapes before they enter context.",
    scope: "User input and free-form tool output.",
    control_mechanism: "A classifier scores each untrusted span; high-scoring spans are stripped or quarantined.",
    failure_behavior: "Fail open — this is a detector, not a gate. It lowers likelihood and never closes the path.",
    implementations: [],
    addresses: ["T-TOOL-ABUSE", "T-CMD-INJECT"]
  }, {
    id: "CTRL-DLP",
    name: "Egress inspection",
    mitigation_class: "detector",
    status: "draft",
    purpose: "Catch known-shape secrets on the way out.",
    scope: "Agent responses and outbound tool payloads.",
    control_mechanism: "Pattern and entropy matching over egress content, with redaction on match.",
    failure_behavior: "Fail open. Detection only.",
    implementations: [],
    addresses: ["T-DATA-LEAK"]
  }],
  styleFields: [{
    entity: "threat",
    field: "title",
    pct: 100
  }, {
    entity: "threat",
    field: "harm",
    pct: 100
  }, {
    entity: "threat",
    field: "weaknesses[].text",
    pct: 100
  }, {
    entity: "threat",
    field: "reachability",
    pct: 62,
    slots: {
      purpose: "Say when this threat is NOT a live path, judged on the un-mitigated architecture.",
      include: ["Open with “NOT applicable if”.", "The architectural fact that removes the path.", "The asset-materiality carve-out, when there is one."],
      avoid: ["A control that mitigates the threat — that belongs in mitigations.", "Hedging (“probably not applicable”).", "More than two carve-outs in one field."],
      example: "NOT applicable if the reachable tools have no operations with real consequences (read-only, no side effects)."
    }
  }, {
    entity: "threat",
    field: "references[]",
    pct: 15
  }, {
    entity: "threat",
    field: "mitre_id",
    pct: 0,
    orphan: true
  }, {
    entity: "mitigation",
    field: "purpose",
    pct: 100
  }, {
    entity: "mitigation",
    field: "control_mechanism",
    pct: 88
  }, {
    entity: "mitigation",
    field: "failure_behavior",
    pct: 54
  }, {
    entity: "mitigation",
    field: "implementations[]",
    pct: 13
  }],
  reports: [{
    system_id: "checkout-agent",
    system_name: "Checkout Agent",
    latest_date: "2026-08-26",
    report_count: 2,
    top_severity: "critical"
  }, {
    system_id: "docs-assistant",
    system_name: "Docs Assistant",
    latest_date: "2026-07-02",
    report_count: 1,
    top_severity: "low"
  }],
  report: {
    system_id: "checkout-agent",
    system_name: "Checkout Agent",
    date: "2026-08-26",
    assessor: "Jane Doe <jane@example.com>",
    system_description: "Answers storefront checkout questions, looks up order status, and now issues refunds under a value cap via the payments API.",
    delta_summary: "Refunds were added as an agent tool. Re-assessed the payment path only; the order-lookup findings from 2026-05-10 were re-checked and the access-control gap is now closed.",
    findings: [{
      id: "T-TOOL-ABUSE",
      severity: "critical",
      likelihood: "high",
      harm: "wrong-decision",
      scenario: "A shopper talks the agent into refunding an order that was never returned; the refund tool fires on model judgement alone and the money leaves before anyone reviews it.",
      source: {
        who: "external-attacker",
        motive: "free goods plus a refund",
        access: "the public storefront chat"
      },
      asset: "refund budget and the payments API",
      attack_surface: "user-agent",
      complexity: "low",
      vulnerability: "the refund tool executes on model decision with no human gate and no check that a return was actually received",
      reasoning: "irreversible money movement, reachable anonymously, and the only thing standing in the way is model judgement",
      delta: "new: no prior agent path could move money; refunds previously required a support agent in the admin console",
      requirements: [{
        id: "CTRL-HACT-CRITICAL",
        status: "needs_implementation"
      }, {
        id: "CTRL-IRREVERSIBLE-ACTION-GUARD",
        status: "needs_implementation"
      }, {
        id: null,
        status: "needs_implementation",
        description: "Refuse a refund unless the warehouse system has recorded the return against that order id."
      }],
      ignored: [{
        id: "CTRL-RATE-LIMITING",
        reason: "throttling slows a refund spree but does not stop the first fraudulent refund, which is already the loss"
      }]
    }, {
      id: "T-DATA-LEAK",
      severity: "medium",
      likelihood: "low",
      harm: "data-exposed",
      scenario: "A shopper asks about another customer order; the agent looks it up and reads back the address and line items.",
      source: {
        who: "external-attacker",
        motive: "harvest customer PII",
        access: "the public storefront chat"
      },
      asset: "customer order records (name, address, line items)",
      attack_surface: "user-agent",
      complexity: "medium",
      vulnerability: "the orders tool takes an order id from model output; scoping depends entirely on the token the tool carries",
      reasoning: "the token is now session-scoped at the gateway, so a cross-customer lookup returns 403 before it reaches the orders service",
      delta: "unchanged by the refund work; carried forward from 2026-05-10 to record that the gap closed",
      requirements: [{
        id: "CTRL-DATA-ACCESS-CONTROL",
        status: "already_covered",
        note: "Closed since the last assessment: the shared API gateway now mints per-session tokens for every storefront agent, so the orders service never sees a broad token."
      }],
      ignored: []
    }],
    discarded: [{
      id: "T-CMD-INJECT",
      reason: "no interpreter, shell or code-execution tool in this deployment"
    }, {
      id: "T-SSRF",
      reason: "the agent calls two fixed internal endpoints; no tool takes a URL from model output"
    }],
    dialogue: [{
      q: "Is there a value cap on the refund tool, and who set it?",
      a: "Payments caps it at 200 EUR per call. Nothing caps calls per session.",
      impact: "Kept the threat at critical: the cap bounds one refund, not a sequence of them, so the loss is not actually bounded."
    }, {
      q: "Does anything verify the goods came back before a refund goes out?",
      a: "No. The agent trusts what the shopper says in chat.",
      impact: "Added the ad hoc requirement about checking the warehouse return record, since no catalog control covers this business rule."
    }, {
      q: "Would rate limiting be enough here?",
      a: "No, the first fraudulent refund is already the loss. Do not list it as a mitigation.",
      impact: "Moved CTRL-RATE-LIMITING to ignored with that reasoning rather than listing it as a partial control."
    }]
  }
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/data.js", error: String((e && e.message) || e) }); }

// ui_kits/authoring-ui/shell.jsx
try { (() => {
const {
  ScreenTabs,
  SearchInput,
  FacetPanel,
  RailRow,
  IconButton,
  Button,
  Badge,
  EmptyState,
  Toast,
  SavedDialog
} = window.KeelDesignSystem_7d5998;
const SCREENS = [["overview", "Overview"], ["threats", "Threats"], ["mitigations", "Mitigations"], ["style", "Style guide"], ["reports", "Reports"]];
function RailHeader({
  title,
  count,
  onNew,
  collapsed,
  onCollapse
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      padding: collapsed ? "12px 0" : "15px 18px",
      borderBottom: "1px solid var(--line-panel)",
      display: "flex",
      alignItems: "center",
      gap: "8px",
      justifyContent: collapsed ? "center" : "flex-start"
    }
  }, /*#__PURE__*/React.createElement(IconButton, {
    glyph: collapsed ? "»" : "«",
    title: collapsed ? "Expand" : "Collapse",
    onClick: onCollapse
  }), collapsed ? null : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--fs-15)",
      margin: 0,
      fontWeight: "var(--fw-bold)",
      letterSpacing: "var(--ls-title)"
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-faint)",
      fontSize: "var(--fs-12)",
      marginLeft: "auto",
      fontVariantNumeric: "var(--numeric)"
    }
  }, count), onNew ? /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    glyph: "\uFF0B",
    onClick: onNew,
    style: {
      marginLeft: "8px"
    }
  }, "New") : null));
}

/** The app frame: one CSS grid, full height, both side tracks user-driven. */
function AppShell({
  screen,
  onScreen,
  rail,
  main,
  preview,
  previewTitle,
  toast,
  saved,
  onCloseSaved
}) {
  const [collapsed, setCollapsed] = React.useState(false);
  const railW = collapsed ? "var(--rail-w-collapsed)" : "var(--rail-w)";
  const prevW = preview ? "var(--preview-w)" : "0px";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: railW + " 1fr " + prevW,
      height: "100vh",
      background: "var(--surface-app)",
      font: "var(--fs-14)/var(--lh-base) var(--font-sans)",
      color: "var(--text-strong)"
    }
  }, /*#__PURE__*/React.createElement("aside", {
    style: {
      background: "var(--surface-panel)",
      borderRight: "1px solid var(--line-panel)",
      display: "flex",
      flexDirection: "column",
      minHeight: 0,
      overflow: "hidden"
    }
  }, collapsed ? null : /*#__PURE__*/React.createElement(ScreenTabs, {
    screens: SCREENS,
    value: screen,
    onChange: onScreen
  }), rail({
    collapsed,
    setCollapsed
  })), /*#__PURE__*/React.createElement("main", {
    style: {
      overflowY: "auto",
      padding: "var(--pad-main)",
      minWidth: 0
    }
  }, main), preview ? /*#__PURE__*/React.createElement("section", {
    style: {
      background: "var(--surface-panel)",
      borderLeft: "1px solid var(--line-panel)",
      overflowY: "auto",
      padding: "20px"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--text-faint)",
      fontWeight: "var(--fw-bold)",
      margin: "0 0 12px"
    }
  }, previewTitle || "Preview"), preview) : null, /*#__PURE__*/React.createElement(Toast, {
    message: toast ? toast.message : "",
    tone: toast && toast.tone,
    show: Boolean(toast)
  }), /*#__PURE__*/React.createElement(SavedDialog, {
    show: Boolean(saved),
    file: saved && saved.file,
    onClose: onCloseSaved,
    repoUrl: "https://github.com/roselis-lab/keel"
  }));
}
function Prose({
  children,
  read
}) {
  return /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      whiteSpace: "pre-wrap",
      fontSize: "var(--fs-14)",
      lineHeight: "var(--lh-prose)",
      color: read ? "var(--text-body-read)" : "var(--text-body)"
    }
  }, children);
}
function PanelCard({
  label,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-panel)",
      border: "1px solid var(--line-panel)",
      borderRadius: "var(--r-10)",
      padding: "var(--pad-section)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: "var(--fs-11)",
      textTransform: "uppercase",
      letterSpacing: "var(--ls-eyebrow)",
      color: "var(--navy-700)",
      margin: "0 0 9px",
      fontWeight: "var(--fw-bold)"
    }
  }, label), children);
}
Object.assign(window, {
  AppShell,
  RailHeader,
  Prose,
  PanelCard,
  SCREENS
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/authoring-ui/shell.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Chip = __ds_scope.Chip;

__ds_ns.Dot = __ds_scope.Dot;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.CoverageBar = __ds_scope.CoverageBar;

__ds_ns.DiffView = __ds_scope.DiffView;

__ds_ns.FacetPanel = __ds_scope.FacetPanel;

__ds_ns.GapChips = __ds_scope.GapChips;

__ds_ns.SeveritySpine = __ds_scope.SeveritySpine;

__ds_ns.RiskBadge = __ds_scope.RiskBadge;

__ds_ns.SplitBar = __ds_scope.SplitBar;

__ds_ns.StatTile = __ds_scope.StatTile;

__ds_ns.EmptyState = __ds_scope.EmptyState;

__ds_ns.ErrorSummary = __ds_scope.ErrorSummary;

__ds_ns.SavedDialog = __ds_scope.SavedDialog;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.WarnBanner = __ds_scope.WarnBanner;

__ds_ns.CheckSet = __ds_scope.CheckSet;

__ds_ns.Field = __ds_scope.Field;

__ds_ns.SearchInput = __ds_scope.SearchInput;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.TextArea = __ds_scope.TextArea;

__ds_ns.TextInput = __ds_scope.TextInput;

__ds_ns.Breadcrumb = __ds_scope.Breadcrumb;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.EditorCard = __ds_scope.EditorCard;

__ds_ns.EntityHeader = __ds_scope.EntityHeader;

__ds_ns.RailRow = __ds_scope.RailRow;

__ds_ns.ScreenTabs = __ds_scope.ScreenTabs;

__ds_ns.SectionBand = __ds_scope.SectionBand;

})();
