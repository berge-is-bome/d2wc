------------------------------------------------------------
-- qubes devilspie2 workspace configurator
-- version 0.1.11.7
-- changes: geometry rules order updated
------------------------------------------------------------



-- USER CUSTOMIZATION
------------------------------------------------------------

-- EXCLUDE, PIN, WORKSPACE_ROUTES, GEOM_RULES, LEFT_EDGE_CORRECTION

-- Accepts (in order of precedence):
--   "domain.class"      (e.g. "personal.okular")
--   "domain"            (e.g. "personal")
--   "class"             (e.g. "xfce4-terminal")

-- Optional disambiguation:
-- In situations where domain and class names are the same, disambiguate using prefixes:
--   "d:<domain>"        will only be matched to a domain
--   "c:<class>"         will only be matched to a class

------------------------------------------------------------
-- Exclusions: anything listed here is ignored
------------------------------------------------------------
local EXCLUDE = {
  -- "work.okular",         -- this domain.class
  "personal-test",       -- domain
  -- "<class_name>",        -- class everywhere
  -- add more here
}

------------------------------------------------------------
-- Pin rules: windows listed here are made visible on all workspaces
------------------------------------------------------------
local PIN = {
  "dom0.xfce4-terminal",
  "dom0.qubes-qube-manager",
  -- "personal",                   -- pin everything from personal
  -- "xfce4-terminal",             -- pin xfce4-terminal everywhere
  -- add more here
}

------------------------------------------------------------
-- Workspace routes. Place applications together on a workspace.
------------------------------------------------------------
local WORKSPACE_ROUTES = {
  [1] = { "personal", "work.navigator", "work.krusader" },
  [2] = { "personal.navigator", "work" },
  -- add more here
}

------------------------------------------------------------
-- Geometry profiles.

-- Geometry profiles determine where something will be placed and what size it will be.
------------------------------------------------------------
local GEOM = {
  wide                  = { x = 100,  y = 456,  w = 3624, h = 1389 },
  centered_mid          = { x = 960,  y = 540,  w = 1200, h = 900  },
  half_left             = { x = 0,    y = 0,    w = 1920, h = 2115 },
  half_right            = { x = 1914, y = 0,    w = 1920, h = 2115 },
  dom0_qubes_app_menu   = { x = 0,    y = 0,    w = 1000, h = 1200,},
  dom0_settings_manager = { x = 830,  y = 517,  w = 1818, h = 1029 },
  custom_name1          = { x = 0,    y = 0,    w = 0,    h = 0    },
  custom_name2          = { x = 0,    y = 0,    w = 0,    h = 0    },
  -- add more here
}

------------------------------------------------------------
-- Geometry rules
------------------------------------------------------------
-- Create a geometry rule and link it to a geometry profile:
--   "domain.class.profile"       (domain specific)
--   "domain.profile"             (all windows from domain)
--   "class.profile"              (global)

-- Class matching rules:
--   - exact match: "okular" matches "okular"
--   - base name:   "soffice" matches "soffice.bin" (drops suffix after first dot)
--   - wildcard:    "soffice*" matches any "soffice.*"
------------------------------------------------------------
local GEOM_RULES = {
  "krusader.wide",
  "kate.half_right",
  "okular.half_right",
  "soffice.centered_mid",           -- matches soffice and soffice.bin

  "personal.okular.half_left",      -- domain-specific override for okular in domain "personal"

  "dom0.qubes-qube-manager.half_left",
  "dom0.xfce4-settings-manager.dom0_settings_manager",
  "dom0.qubes-app-menu.dom0_qubes_app_menu",
  -- add more here
}

------------------------------------------------------------
-- Left-edge window position correction
-- Map specific "domain.class" to a correction mode when the target X is 0.
-- Values:
--   "pos1"  -> call set_window_position(x, y)
--   "pos2"  -> call set_window_position2(x, y)
-- If a domain.class key is not present, no correction is applied.
-- Use lowercase names; keys are matched against domain and class as detected by devilspie2.
------------------------------------------------------------
local LEFT_EDGE_CORRECTION = {
  ["dom0.qubes-qube-manager"] = "pos1",
  ["personal.okular"]         = "pos2",
  -- add more here
}



-- PROGRAM LOGIC
------------------------------------------------------------

-- Only act on real app windows
-- Filters out non-normal windows like menus, splash screens, panels, and notifications so only real application windows are processed.
------------------------------------------------------------
if (get_window_type() ~= "WINDOW_TYPE_NORMAL") then
  return
end

------------------------------------------------------------
-- Token parser and lookup builders
------------------------------------------------------------
local function parse_token(token)
  local t = (token or ""):lower()
  local tag, rest = t:match("^([dc]):(.+)$")
  if tag == "d" then return "domain", rest end
  if tag == "c" then return "class",  rest end
  local d, c = t:match("^([^%.]+)%.(.+)$")
  if d and c then return "exact", d .. "." .. c end
  return "domain", t
end

------------------------------------------------------------
-- Build lookups for EXCLUDE
------------------------------------------------------------
local EX_EXACT, EX_DOMAIN, EX_CLASS = {}, {}, {}
for _, tok in ipairs(EXCLUDE) do
  if tok ~= nil and tok ~= "" then
    local kind, val = parse_token(tok)
    if     kind == "exact"  then EX_EXACT[val]   = true
    elseif kind == "domain" then EX_DOMAIN[val]  = true
    elseif kind == "class"  then EX_CLASS[val]   = true
    end
  end
end

------------------------------------------------------------
-- Build lookups for PIN
------------------------------------------------------------
local PIN_EXACT, PIN_DOMAIN, PIN_CLASS = {}, {}, {}
for _, tok in ipairs(PIN) do
  if tok ~= nil and tok ~= "" then
    local kind, val = parse_token(tok)
    if     kind == "exact"  then PIN_EXACT[val]   = true
    elseif kind == "domain" then PIN_DOMAIN[val]  = true
    elseif kind == "class"  then PIN_CLASS[val]   = true
    end
  end
end

------------------------------------------------------------
-- Build lookups for WORKSPACE_ROUTES
------------------------------------------------------------
local WS_EXACT, WS_DOMAIN, WS_CLASS = {}, {}, {}
for wsnum, list in pairs(WORKSPACE_ROUTES) do
  for _, tok in ipairs(list) do
    if tok ~= nil and tok ~= "" then
      local kind, val = parse_token(tok)
      if     kind == "exact"  then WS_EXACT[val]  = wsnum
      elseif kind == "domain" then WS_DOMAIN[val] = wsnum
      elseif kind == "class"  then WS_CLASS[val]  = wsnum
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
-- Apply exclusions
------------------------------------------------------------
-- Optional domain/class/domain.class exclusion. If enabled, the script will not touch workspace or geometry.
if domain then
  local key = domain .. "." .. cls
  if EX_EXACT[key] or EX_DOMAIN[domain] or EX_CLASS[cls] then
    -- debug_print("excluded: " .. key)
    return
  end
end

------------------------------------------------------------
-- Workspace configuration
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
-- Pin windows (sticky on all workspaces).
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
------------------------------------------------------------
-- Maps:
--   GR_DOMAIN_CLASS[domain][class_pattern] = profile
--   GR_DOMAIN_WIDE[domain]                 = profile
--   GR_GLOBAL_CLASS[class_pattern]         = profile
local GR_DOMAIN_CLASS, GR_DOMAIN_WIDE, GR_GLOBAL_CLASS = {}, {}, {}

local function add_geom_rule(tok)
  local t = (tok or ""):lower()

  -- Split off profile from the rightmost dot
  local stem, prof = t:match("^(.*)%.([^%.]+)$")
  if not stem or not prof then
    debug_print("GEOM_RULES: could not parse '" .. tostring(tok) .. "'")
    return
  end

  -- Disambiguators first
  local tag, rest = stem:match("^([dc]):(.+)$")
  if tag == "d" then
    -- domain.profile
    if rest ~= "" then GR_DOMAIN_WIDE[rest] = prof; return end
  elseif tag == "c" then
    -- class.profile
    if rest ~= "" then GR_GLOBAL_CLASS[rest] = prof; return end
  end

  -- domain.class.profile (class may contain dots)
  local d, c = stem:match("^([^%.]+)%.(.+)$")
  if d and c then
    GR_DOMAIN_CLASS[d] = GR_DOMAIN_CLASS[d] or {}
    GR_DOMAIN_CLASS[d][c] = prof
    return
  end

  -- two-part default -> class.profile
  GR_GLOBAL_CLASS[stem] = prof
end

for _, tok in ipairs(GEOM_RULES) do
  add_geom_rule(tok)
end

local function class_match_rank(rule_cls, actual_cls)
  -- exact match
  if rule_cls == actual_cls then return 3 end
  -- wildcard prefix, e.g. "soffice*"
  if rule_cls:sub(-1) == "*" then
    local pref = rule_cls:sub(1, -2)
    if actual_cls:sub(1, #pref) == pref then return 2 end
  end
  -- base-name match: "soffice" vs "soffice.bin"
  local base = actual_cls:gsub("%..*$", "")
  if rule_cls == base then return 1 end
  return 0
end

local function pick_profile(map, actual_cls)
  if not map then return nil end
  local best_p, best_r = nil, 0
  for rule_cls, prof in pairs(map) do
    local r = class_match_rank(rule_cls, actual_cls)
    if r > best_r then
      best_r, best_p = r, prof
    end
  end
  return best_p
end

-- Resolve geometry with precedence:
--   domain.class.profile -> domain.profile -> class.profile
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
    debug_print("GEOM_RULES: unknown profile '" .. tostring(prof) .. "'")
  end
  return g
end

-- Apply window geometry
local g = find_geometry(domain, cls)
if g then
  set_window_geometry(g.x, g.y, g.w, g.h)

  -- Per-domain.class left-edge correction when target x == 0
  if g.x == 0 and domain and cls then
    local key = domain .. "." .. cls
    local corr = LEFT_EDGE_CORRECTION[key]
    if corr == "pos1" then
      set_window_position(g.x, g.y)
    elseif corr == "pos2" then
      set_window_position2(g.x, g.y)
    end
  end

  -- debug_print(string.format("geometry: %s/%s -> %dx%d+%d+%d", tostring(domain), cls, g.w, g.h, g.x, g.y))
end
