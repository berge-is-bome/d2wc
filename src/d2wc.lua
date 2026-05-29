------------------------------------------------------------
-- d2wc managed
-- devilspie2 workspace configurator
-- version 0.1.12.4
-- changes: Lua event handoff proof launches bare d2wc from supported window-open events
-- version 0.1.12.3
-- changes: prefixed grammar (d:, c:, g:, le:) with space-separated tokens
-- version 0.1.12.2
-- Split a dotted class string into tokens, e.g. "org.gnome.meld" -> {"org","gnome","meld"}
-- Class matching improved to recognize class names within dotted segments of class names
------------------------------------------------------------


-- USER CUSTOMIZATION
------------------------------------------------------------

-- Lua event handoff proof.
-- When enabled, supported window-open events launch the d2wc configurator.
-- The d2wc configurator window class is suppressed to avoid recursive configurator launches.
local D2WC_EVENT_HANDOFF_ENABLED = true
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"

-- EXCLUDE, PIN, WORKSPACE_ROUTES, WORKSPACE_PLACEMENT, LEFT_EDGE_CORRECTION
-- All rules use space-separated tokens with explicit prefixes:
--   d:<domain>   c:<class>   g:<geom_profile>   le:<pos1|pos2>
-- Order of tokens does not matter. Case-insensitive.
--
-- Matching precedence everywhere:  domain.class  ->  domain  ->  class
-- Duplicates within a single rule (e.g., two g: tokens) are invalid; they are skipped with a debug message.
-- Unknown geometry profile in g: is invalid; skipped with a debug message.

------------------------------------------------------------
-- Exclusions: anything listed here is ignored
------------------------------------------------------------
local EXCLUDE = {
  -- "d:work c:okular",    -- this domain.class
  "d:personal-test",       -- domain
  -- "c:<class_name>",     -- class everywhere
  -- add more here
}

------------------------------------------------------------
-- Pin rules: windows listed here are made visible on all workspaces
------------------------------------------------------------
local PIN = {
  "d:dom0 c:xfce4-terminal",         -- pin dom0 xfce4-terminal windows
  "d:dom0 c:qubes-qube-manager",     -- pin Qube Manager
  -- "d:personal",                   -- pin everything from personal
  -- "c:xfce4-terminal",             -- pin xfce4-terminal everywhere
  -- add more here
}

------------------------------------------------------------
-- Workspace routes. Place application windows on a specific workspace.
-- NOTE: Only one list per workspace key is allowed.
-- NOTE In Lua, later duplicates overwrite earlier ones.
------------------------------------------------------------
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", "d:work c:navigator", "d:work c:krusader", },

  [2] = { "d:personal c:navigator", "d:work", },
  -- add more here
}

------------------------------------------------------------
-- Geometry profiles.
-- Geometry profiles determine where a window will be placed and what size it will be.
------------------------------------------------------------
local GEOM = {
  wide                  = { x = 100,  y = 456,  w = 3624, h = 1389 },
  centered_mid          = { x = 960,  y = 540,  w = 1200, h = 900  },
  half_left             = { x = 0,    y = 0,    w = 1920, h = 2115 },
  half_right            = { x = 1914, y = 0,    w = 1920, h = 2115 },

  dom0_qubes_app_menu   = { x = 0,    y = 0,    w = 1000, h = 1200 },
  dom0_settings_manager = { x = 830,  y = 517,  w = 1818, h = 1029 },

  dom0_template_manager = { x = 1129, y = 0  ,  w = 1220, h = 2115 },
  dom0_new_qube         = { x = 0   , y = 387 , w = 1920, h = 1200 },
  dom0_global_config    = { x = 0   , y = 0   , w = 1920, h = 1800 },
  -- add more here
}

------------------------------------------------------------
-- Workspace placement rules
------------------------------------------------------------
-- Link application windows to geometry profiles using g:.
-- At least one domain or class must be specified with a geometry profile.

-- Class matching rules:
-- exact match: "okular" matches "okular"
-- base name:   "soffice" matches "soffice.bin" (drops suffix after first dot)
-- wildcard:    "soffice*" matches any "soffice.*"
------------------------------------------------------------
local WORKSPACE_PLACEMENT = {
  "c:krusader g:wide",     -- krusader will use the `wide` GEOM profile everywhere it is opened
  "c:soffice g:centered_mid",     -- office will use the `centered_mid` GEOM profile everywhere it is opened
  "c:okular g:half_right",     -- okular will use the `half_right` GEOM profile everywhere it is opened
  "c:kate g:half_right",

  "d:personal c:okular g:half_left",    -- domain-specific override for okular in domain personal

  "d:dom0 c:qubes-qube-manager g:half_left",
  "d:dom0 c:xfce4-settings-manager g:dom0_settings_manager",
  "d:dom0 c:qubes-app-menu g:dom0_qubes_app_menu",    -- domain-specific override for qubes-app-menu in dom0
  -- add more here
}

------------------------------------------------------------
-- Left-edge window position correction

-- Sometimes when a window is positioned at `x = 0`, the devilspie2 function set_window_geometry()
-- does not place the window at exactly `x = 0`, but a few pixels off from 0.

-- Map targets to a correction mode when the target X is 0, but window placement is slightly off.

-- Values:  le:pos1  -> set_window_position(x, y)
--          le:pos2  -> set_window_position2(x, y)

-- At least one of d: or c: must be present.
------------------------------------------------------------
local LEFT_EDGE_CORRECTION = {
  "d:dom0 c:qubes-qube-manager le:pos1",
  "d:personal c:okular le:pos2",
  -- add more here
}



-- PROGRAM LOGIC
------------------------------------------------------------

-- Only act on real app windows
-- Filters out non-normal windows like menus, splash screens, panels, and notifications so only real application windows are processed.
------------------------------------------------------------
local window_type = get_window_type()
if (window_type ~= "WINDOW_TYPE_NORMAL") then
  return
end

------------------------------------------------------------
-- Helpers
------------------------------------------------------------
local function lc(s) return (s or ""):lower() end

local function launch_d2wc_event_handoff(event_class)
  if not D2WC_EVENT_HANDOFF_ENABLED then return end
  if event_class == D2WC_CONFIGURATOR_CLASS then return end

  os.execute("d2wc >/dev/null 2>&1 &")
end

-- Split a rule string into prefixed tokens and validate duplicates.
-- Returns { d=..., c=..., g=..., le=... }, is_valid
local function parse_prefixed_rule(rule_str)
  local seen = {}
  local out = {}
  for token in lc(rule_str):gmatch("%S+") do
    local k, v = token:match("^([a-z]+):(.*)$")
    if not k or v == "" then
      debug_print("parse: invalid token '" .. tostring(token) .. "' in '" .. tostring(rule_str) .. "'")
      return {}, false
    end
    if k ~= "d" and k ~= "c" and k ~= "g" and k ~= "le" then
      debug_print("parse: unknown prefix '" .. k .. "' in '" .. tostring(rule_str) .. "'")
      return {}, false
    end
    if seen[k] then
      debug_print("parse: duplicate '" .. k .. ":' in '" .. tostring(rule_str) .. "'; skipping rule")
      return {}, false
    end
    seen[k] = true
    out[k] = v
  end
  return out, true
end

-- Split a dotted class string into tokens, e.g. "org.gnome.meld" -> {"org","gnome","meld"}
local function split_dotted(s)
  local t = {}
  for part in (s or ""):gmatch("[^%.]+") do
    t[#t+1] = part
  end
  return t
end

-- Class matching
-- Rank quality of a rule class pattern vs an actual class string.
-- Priority:
--   4 = exact match on full string (e.g. "org.gnome.meld")
--   3 = exact match on any dotted segment (e.g. "meld")
--   2 = wildcard prefix on full string (e.g. "org.gnome.*")
--   1 = wildcard prefix on any segment (e.g. "mel*")
--   0 = no match
local function class_match_rank(rule_cls, actual_cls)
  -- 4) exact full-string match
  if rule_cls == actual_cls then return 4 end

  local tokens = split_dotted(actual_cls)

  -- 3) exact match on any segment
  for _, seg in ipairs(tokens) do
    if rule_cls == seg then return 3 end
  end

  -- wildcard support
  if rule_cls:sub(-1) == "*" then
    local pref = rule_cls:sub(1, -2)

    -- 2) wildcard on full string
    if actual_cls:sub(1, #pref) == pref then return 2 end

    -- 1) wildcard on any segment
    for _, seg in ipairs(tokens) do
      if seg:sub(1, #pref) == pref then return 1 end
    end
  end

  return 0
end

local function pick_profile(map, actual_cls)
  if not map then return nil end
  local best_p, best_r = nil, 0
  for rule_cls, prof in pairs(map) do
    local r = class_match_rank(rule_cls, actual_cls)
    if r > best_r then best_r, best_p = r, prof end
  end
  return best_p
end

------------------------------------------------------------
-- Build lookups for EXCLUDE
------------------------------------------------------------
local EX_EXACT, EX_DOMAIN, EX_CLASS = {}, {}, {}

for _, rule in ipairs(EXCLUDE) do
  if rule and rule ~= "" then
    local R, ok = parse_prefixed_rule(rule)
    if ok then
      local d, c = R.d, R.c
      if d and c then
        local key = d .. "." .. c
        if EX_EXACT[key] then
          debug_print("EXCLUDE: duplicate exact '" .. key .. "'")
        else
          EX_EXACT[key] = true
        end
      elseif d then
        if EX_DOMAIN[d] then
          debug_print("EXCLUDE: duplicate domain '" .. d .. "'")
        else
          EX_DOMAIN[d] = true
        end
      elseif c then
        if EX_CLASS[c] then
          debug_print("EXCLUDE: duplicate class '" .. c .. "'")
        else
          EX_CLASS[c] = true
        end
      else
        debug_print("EXCLUDE: rule needs d: or c: -> '" .. rule .. "'")
      end
    end
  end
end

------------------------------------------------------------
-- Build lookups for PIN
------------------------------------------------------------
local PIN_EXACT, PIN_DOMAIN, PIN_CLASS = {}, {}, {}

for _, rule in ipairs(PIN) do
  if rule and rule ~= "" then
    local R, ok = parse_prefixed_rule(rule)
    if ok then
      local d, c = R.d, R.c
      if d and c then
        local key = d .. "." .. c
        if PIN_EXACT[key] then
          debug_print("PIN: duplicate exact '" .. key .. "'")
        else
          PIN_EXACT[key] = true
        end
      elseif d then
        if PIN_DOMAIN[d] then
          debug_print("PIN: duplicate domain '" .. d .. "'")
        else
          PIN_DOMAIN[d] = true
        end
      elseif c then
        if PIN_CLASS[c] then
          debug_print("PIN: duplicate class '" .. c .. "'")
        else
          PIN_CLASS[c] = true
        end
      else
        debug_print("PIN: rule needs d: or c: -> '" .. rule .. "'")
      end
    end
  end
end

------------------------------------------------------------
-- Build lookups for WORKSPACE_ROUTES
-- NOTE: Only one list per workspace key is allowed.
------------------------------------------------------------
local WS_EXACT, WS_DOMAIN, WS_CLASS = {}, {}, {}

for wsnum, list in pairs(WORKSPACE_ROUTES) do
  for _, rule in ipairs(list) do
    if rule and rule ~= "" then
      local R, ok = parse_prefixed_rule(rule)
      if ok then
        local d, c = R.d, R.c
        if d and c then
          local key = d .. "." .. c
          if WS_EXACT[key] then
            debug_print("WORKSPACE_ROUTES[" .. wsnum .. "]: duplicate exact '" .. key .. "'")
          else
            WS_EXACT[key] = wsnum
          end
        elseif d then
          if WS_DOMAIN[d] then
            debug_print("WORKSPACE_ROUTES[" .. wsnum .. "]: duplicate domain '" .. d .. "'")
          else
            WS_DOMAIN[d] = wsnum
          end
        elseif c then
          if WS_CLASS[c] then
            debug_print("WORKSPACE_ROUTES[" .. wsnum .. "]: duplicate class '" .. c .. "'")
          else
            WS_CLASS[c] = wsnum
          end
        else
          debug_print("WORKSPACE_ROUTES[" .. wsnum .. "]: rule needs d: and/or c: -> '" .. rule .. "'")
        end
      end
    end
  end
end

------------------------------------------------------------
-- Qubes domain and class extraction
------------------------------------------------------------
-- Read domain; treat "" as dom0; if nil, skip workspace assignment but still allow global geometry rules
local raw_domain = get_window_property("_QUBES_VMNAME")
local domain
if raw_domain == "" then
  domain = "dom0"
elseif raw_domain ~= nil then
  domain = raw_domain
else
  debug_print("_QUBES_VMNAME is nil; skipping domain-based workspace")
end
-- Normalize to lowercase for consistent matching
if domain then domain = domain:lower() end

-- Class helper: get WM_CLASS class part in lowercase (after the last colon)
local function get_lower_class()
  local s = (get_class_instance_name() or ""):lower()
  return s:match(".*:([^:]+)$") or s
end

local cls = get_lower_class()

------------------------------------------------------------
-- Lua event handoff proof
------------------------------------------------------------
launch_d2wc_event_handoff(cls)

------------------------------------------------------------
-- Apply exclusions
------------------------------------------------------------
if domain then
  local key = domain .. "." .. cls
  if EX_EXACT[key] or EX_DOMAIN[domain] or EX_CLASS[cls] then
    -- debug_print("excluded: " .. key)
    return
  end
end

------------------------------------------------------------
-- Workspace routing
-- Precedence: domain.class -> domain -> class
------------------------------------------------------------
local function compute_workspace(d, c)
  if not d then return nil end
  local key = d .. "." .. c
  return WS_EXACT[key] or WS_DOMAIN[d] or WS_CLASS[c]
end

-- Assign workspace
if domain then
  local ws = compute_workspace(domain, cls)
  if ws and ws > 0 and ws <= get_workspace_count() then
    set_window_workspace(ws)
  end
end

------------------------------------------------------------
-- Pin windows
-- Pinning is done after workspace assignment, because workspace assignment removes the sticky flag.
------------------------------------------------------------
if domain then
  local key = domain .. "." .. cls
  if PIN_EXACT[key] or PIN_DOMAIN[domain] or PIN_CLASS[cls] then
    pin_window()
    -- debug_print(("pinned: dom=%s cls=%s"):format(tostring(domain), cls))
  end
end

------------------------------------------------------------
-- Build geometry rule maps and resolvers
-- Maps:
--   GR_DOMAIN_CLASS[domain][class_pattern] = profile
--   GR_DOMAIN_WIDE[domain]                 = profile
--   GR_GLOBAL_CLASS[class_pattern]         = profile
------------------------------------------------------------
local GR_DOMAIN_CLASS, GR_DOMAIN_WIDE, GR_GLOBAL_CLASS = {}, {}, {}

for _, rule in ipairs(WORKSPACE_PLACEMENT) do
  if rule and rule ~= "" then
    local R, ok = parse_prefixed_rule(rule)
    if ok then
      local d, c, prof = R.d, R.c, R.g
      if not prof then
        debug_print("WORKSPACE_PLACEMENT: missing g: in '" .. rule .. "'")
      elseif not GEOM[prof] then
        debug_print("WORKSPACE_PLACEMENT: unknown profile '" .. prof .. "' in '" .. rule .. "'")
      elseif not d and not c then
        debug_print("WORKSPACE_PLACEMENT: rule needs d: or c: -> '" .. rule .. "'")
      else
        if d and c then
          GR_DOMAIN_CLASS[d] = GR_DOMAIN_CLASS[d] or {}
          if GR_DOMAIN_CLASS[d][c] then
            debug_print("WORKSPACE_PLACEMENT: duplicate domain.class '" .. d .. "." .. c .. "'")
          else
            GR_DOMAIN_CLASS[d][c] = prof
          end
        elseif d then
          if GR_DOMAIN_WIDE[d] then
            debug_print("WORKSPACE_PLACEMENT: duplicate domain '" .. d .. "'")
          else
            GR_DOMAIN_WIDE[d] = prof
          end
        elseif c then
          if GR_GLOBAL_CLASS[c] then
            debug_print("WORKSPACE_PLACEMENT: duplicate class '" .. c .. "'")
          else
            GR_GLOBAL_CLASS[c] = prof
          end
        end
      end
    end
  end
end

-- Resolve geometry for domain+class using WORKSPACE_PLACEMENT:
-- Precedence: domain.class -> domain -> class
local function find_geometry(d, class_lc)
  local prof = nil
  if d and GR_DOMAIN_CLASS[d] then
    prof = pick_profile(GR_DOMAIN_CLASS[d], class_lc)
  end
  if not prof and d and GR_DOMAIN_WIDE[d] then
    prof = GR_DOMAIN_WIDE[d]
  end
  if not prof then
    prof = pick_profile(GR_GLOBAL_CLASS, class_lc)
  end
  if not prof then return nil end
  local g = GEOM[prof]
  if not g then
    debug_print("WORKSPACE_PLACEMENT: unknown profile '" .. tostring(prof) .. "'")
  end
  return g
end

------------------------------------------------------------
-- Build left edge correction lookups
-- Precedence: domain.class -> domain -> class
------------------------------------------------------------
local LEC_EXACT, LEC_DOMAIN, LEC_CLASS = {}, {}, {}

for _, rule in ipairs(LEFT_EDGE_CORRECTION) do
  if rule and rule ~= "" then
    local R, ok = parse_prefixed_rule(rule)
    if ok then
      local d, c, mode = R.d, R.c, R.le
      if not mode or (mode ~= "pos1" and mode ~= "pos2") then
        debug_print("LEFT_EDGE_CORRECTION: missing or invalid le: in '" .. rule .. "'")
      elseif not d and not c then
        debug_print("LEFT_EDGE_CORRECTION: rule needs d: or c: -> '" .. rule .. "'")
      else
        if d and c then
          local key = d .. "." .. c
          if LEC_EXACT[key] then
            debug_print("LEFT_EDGE_CORRECTION: duplicate exact '" .. key .. "'")
          else
            LEC_EXACT[key] = mode
          end
        elseif d then
          if LEC_DOMAIN[d] then
            debug_print("LEFT_EDGE_CORRECTION: duplicate domain '" .. d .. "'")
          else
            LEC_DOMAIN[d] = mode
          end
        elseif c then
          if LEC_CLASS[c] then
            debug_print("LEFT_EDGE_CORRECTION: duplicate class '" .. c .. "'")
          else
            LEC_CLASS[c] = mode
          end
        end
      end
    end
  end
end

------------------------------------------------------------
-- Apply window geometry
------------------------------------------------------------
local g = find_geometry(domain, cls)
if g then
  set_window_geometry(g.x, g.y, g.w, g.h)

  -- Per target left-edge correction when target x == 0
  if g.x == 0 and domain and cls then
    local key = domain .. "." .. cls
    local corr = LEC_EXACT[key] or LEC_DOMAIN[domain] or LEC_CLASS[cls]
    if corr == "pos1" then
      set_window_position(g.x, g.y)
    elseif corr == "pos2" then
      set_window_position2(g.x, g.y)
    end
  end

  -- debug_print(string.format("geometry: %s/%s -> %dx%d+%d+%d", tostring(domain), cls, g.w, g.h, g.x, g.y))
end
