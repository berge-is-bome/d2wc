------------------------------------------------------------
-- qubes devilspie2 workspace configurator
-- version 0.1.11.5
------------------------------------------------------------



-- USER CUSTOMIZATION
------------------------------------------------------------

-- EXCLUDE, PIN, WORKSPACE_ROUTES, WORKSPACE_CONFIGURATOR, LEFT_EDGE_CORRECTION

-- Accepts:
--   "domain"            (e.g. "personal")
--   "class"             (e.g. "okular")
--   "domain.class"      (e.g. "personal.okular")

-- Optional disambiguation:
-- In situations where domain and class names are the same, disambiguate using prefixes:
--   "d:<domain>"        name given will only be matched to a domain
--   "c:<class>"         name given will only be matched to a class

------------------------------------------------------------
-- Exclusions: anything listed here is ignored
------------------------------------------------------------
local EXCLUDE = {
  "personal-test",       -- whole domain
  -- "c:qubes-app-menu",    -- class everywhere
  -- "personal.okular",     -- only this domain.class
}

------------------------------------------------------------
-- Pin rules: windows listed here are made visible on all workspaces
------------------------------------------------------------
local PIN = {
  "dom0.xfce4-terminal",
  "dom0.qubes-qube-manager",
  -- "d:personal",        -- pin everything from personal
  -- "c:okular",          -- pin okular everywhere
}

------------------------------------------------------------
-- Workspace routes. Place applications together on a workspace.
------------------------------------------------------------
local WORKSPACE_ROUTES = {
  [1] = { "personal", "work.navigator", "work.krusader" },
  -- [2] = { "test.okular", "d:business-clients", "c:okular" },
}

------------------------------------------------------------
-- Geometry profiles.
--
--
--
--
--
------------------------------------------------------------
local GEOM = {
  wide         = { x = 100,  y = 456,  w = 3624, h = 1389 },
  centered_mid = { x = 960,  y = 540,  w = 1200, h = 900  },
  half_left    = { x = 0,    y = 0,    w = 1920, h = 2115 },
  half_right   = { x = 1913, y = 0,    w = 1920, h = 2115 },
  custom_name  = { x = 0,    y = 0,    w = 0,    h = 0    },
}

------------------------------------------------------------
-- Workspace configuration with easy tokens
------------------------------------------------------------
-- Each entry is either:
--   "profile.class"              (global)
--   "domain.profile.class"       (domain specific)
-- Class matching rules:
--   - exact match: "okular" matches "okular"
--   - base name:   "soffice" matches "soffice.bin" (drops suffix after first dot)
--   - wildcard:    "soffice*" matches any "soffice.*"
--
-- Examples:
--   wide.krusader
--   wide.soffice
--   half_right.okular
--   personal.half_left.okular
--
-- Example: domain-specific override for okular in domain "personal"
--   personal.centered_mid.okular
------------------------------------------------------------
local GEOM_RULES = {
  "wide.krusader",
  "wide.soffice",            -- matches soffice and soffice.bin

  "half_right.okular",

  "personal.half_left.okular",
  "dom0.half_left.qubes-qube-manager"
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
  -- ["personal.okular"] = "pos2",
  -- ["dom0.krusader"]   = "pos1",
  ["dom0.qubes-qube-manager"] = "pos1",
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
-- Build rule maps and resolvers
------------------------------------------------------------
local GR_DOMAIN, GR_GLOBAL = {}, {}

local function add_geom_rule(tok)
  local t = (tok or ""):lower()
  -- domain.profile.class
  local d, p, c = t:match("^([^%.]+)%.([^%.]+)%.(.+)$")
  if d and p and c then
    GR_DOMAIN[d] = GR_DOMAIN[d] or {}
    GR_DOMAIN[d][c] = p
    return
  end
  -- profile.class
  local p2, c2 = t:match("^([^%.]+)%.(.+)$")
  if p2 and c2 then
    GR_GLOBAL[c2] = p2
    return
  end
  debug_print("GEOM_RULES: could not parse '" .. tostring(tok) .. "'")
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

-- Resolve geometry for domain+class using GEOM_RULES
local function find_geometry(d, class_lc)
  local prof = nil
  if d and GR_DOMAIN[d] then
    prof = pick_profile(GR_DOMAIN[d], class_lc)
  end
  if not prof then
    prof = pick_profile(GR_GLOBAL, class_lc)
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
