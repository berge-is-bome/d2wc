------------------------------------------------------------
-- qdwc = qubes devilspie2 workspace configurator
-- version 0.1.8
------------------------------------------------------------

-- Only act on real app windows
if (get_window_type() ~= "WINDOW_TYPE_NORMAL") then
  return
end

-- Exclusions: anything listed here is ignored completely
local EXCLUDE = {
  domains = {
    -- ["some-domain"] = true,   -- optional domain exclusion
  },
  classes = {
    -- ["some-class"] = true,     -- optional class-level exclude
    ["qubes-app-menu"] = true,     -- optional class-level exclude
  },
}

-- Pin rules: pin window from a domain, or, all windows from a domain, making them visible on all workspaces
local PIN = {
  ["dom0"] = { ["xfce4-terminal"] = true, ["qubes-qube-manager"] = true, }, -- pinned dom0 applications
  -- ["personal"] = true, -- pin everything from personal
  -- ["personal"] = { ["okular"] = true },              -- pin one class from personal
}

-- Workspace by Qubes domain
local workspaceAssociation = {
  ["dom0"] = 1,
  ["personal"] = 1,
  ["test"] = 4,
  ["business"] = 2,
  ["business-clients"] = 2,
  ["customer"] = 3,
}

-- Workspace routes. Place applications together on a workspace.
-- Keys are workspace numbers; values are lists of "domain.class".
-- Examples with hyphens in domain names are fine because these are strings.
local WORKSPACE_ROUTES = {
  [1] = { "personal", "work.navigator", "work.krusader" },
  -- [2] = { "test.okular", "business-clients.okular" },
}

-- Left-edge window poition correction for windows that are positioned at x == 0
-- "none" -> do not adjust after set_window_geometry
-- "pos1" -> call set_window_position(x, y)
-- "pos2" -> call set_window_position2(x, y)
local LEFT_EDGE_CORRECTION = "pos2"   -- change to "pos1" or "pos2" if you see a left gap when x = 0

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

-- Optional domain exclusion: act as if devilspie2 is not running
if domain and EXCLUDE.domains[domain] then
  -- debug_print("excluded domain: " .. domain)
  return
end

-- Class helper: get WM_CLASS class part in lowercase (after the last colon)
local function get_lower_class()
  local s = (get_class_instance_name() or ""):lower()
  return s:match(".*:([^:]+)$") or s
end

local cls = get_lower_class()

-- Optional class exclusion. If enabled, the script will not touch workspace or geometry.
if EXCLUDE.classes[cls] then
  -- debug_print("excluded class: " .. cls)
  return
end

-- Assign workspace only if we have a domain
if domain then
  local ws = workspaceAssociation[domain]
  if ws and ws > 0 and ws <= get_workspace_count() then
    set_window_workspace(ws)
  end
end

-- Pin windows (sticky on all workspaces).
-- Pinning is done after workspace assignment, because workspace assignment removes the sticky flag.
local should_pin = false
if domain and PIN[domain] ~= nil then
  local rule = PIN[domain]
  if rule == true then
    should_pin = true
  elseif type(rule) == "table" and rule[cls] then
    should_pin = true
  end
end

if should_pin then
  pin_window()
  debug_print(("pinned: dom=%s cls=%s"):format(tostring(domain), cls))
end

------------------------------------------------------------
-- Geometry profiles and Rules
-- 1) Geometry profiles
-- 2) Group applications by Geometry profile
-- 3) Optionally override per domain or per class
------------------------------------------------------------

------------------------------------------------------------
-- 1_ Geometry profiles
------------------------------------------------------------
local GEOM = {
  wide         = { x = 100,  y = 456,  w = 3624, h = 1389 },
  centered_mid = { x = 960,  y = 540,  w = 1200, h = 900  },
  half_left    = { x = 0,    y = 0,    w = 1920, h = 2115 },
  half_right   = { x = 1913, y = 0,    w = 1920, h = 2115 },
  custom_name  = { x = 0,    y = 0,    w = 0,    h = 0    },
}

------------------------------------------------------------
-- 2+3) RULES
-- ["*"] is global defaults
-- In per_class you can supply either:
--   a) a geometry profile, e.g. "half_right"
--   b) a geometry table { x=..., y=..., w=..., h=... }
-- Example: domain-specific override for okular. Use this rule to override global defaults per domain
------------------------------------------------------------
local RULES = {
  ["*"] = {
    groups = {
      wide       = { "krusader" }, -- shared geometry
      half_right = { "okular" }, -- shared geometry
      -- wide       = { "krusader", "okular" },  -- shared geometry
    },
    per_class = {
      -- ["okular"] = "half_right", -- geometry profile
      -- ["gimp-3.0"] = { x = 120, y = 120, w = 1600, h = 1000 }, -- numerical values
    },
  },

  test = {
    groups = {
      half_left = { "some-application", "another-application" }, -- shared geometry
    },
    per_class = {
      -- ["some-application"] = "half_right", -- geometry profile
      -- ["some-application"] = { x = 0, y = 0, w = 1280, h = 900 }, -- numerical values
    },
  },

  ["personal"] = {
    groups = {
    -- you can still group (other) applications here if you want
    },
    per_class = {
    ["okular"] = "half_left",
    },
  },

  -- Example: domain-specific override for okular in domain "personal"
  -- personal = {
  --   groups = {
      -- you can still group (other) applications here if you want
  --   per_class = {
      -- Option A: geometry profile
      -- ["okular"] = "centered_mid",

      -- Option B: numerical values
      -- ["okular"] = { x = 1913, y = 0, w = 1920, h = 2115 },
  --   },
  -- },
}

------------------------------------------------------------
-- Resolver helpers
------------------------------------------------------------
local function in_list(list, needle)
  for _, v in ipairs(list or {}) do
    if v == needle then return true end
  end
  return false
end

local function resolve_geom_spec(spec)
  if type(spec) == "string" then
    local g = GEOM[spec]
    if not g then
      debug_print("RULES: unknown profile '" .. spec .. "'")
    end
    return g
  elseif type(spec) == "table" then
    if spec.x and spec.y and spec.w and spec.h then
      return spec
    else
      debug_print("RULES: bad geometry table for class")
      return nil
    end
  else
    return nil
  end
end

-- Resolve geometry for domain+class, then global defaults
local function find_geometry(d, class_lc)
  -- 1) domain-specific per_class
  local rd = d and RULES[d] or nil
  if rd then
    if rd.per_class and rd.per_class[class_lc] ~= nil then
      local g = resolve_geom_spec(rd.per_class[class_lc])
      if g then return g end
    end
    -- 2) domain-specific groups
    if rd.groups then
      for prof, list in pairs(rd.groups) do
        if in_list(list, class_lc) then
          return GEOM[prof]
        end
      end
    end
  end

  -- 3) global per_class
  local rdef = RULES["*"]
  if rdef and rdef.per_class and rdef.per_class[class_lc] ~= nil then
    local g = resolve_geom_spec(rdef.per_class[class_lc])
    if g then return g end
  end

  -- 4) global groups
  if rdef and rdef.groups then
    for prof, list in pairs(rdef.groups) do
      if in_list(list, class_lc) then
        return GEOM[prof]
      end
    end
  end

  return nil
end

-- Apply window geometry
local g = find_geometry(domain, cls)
if g then
  set_window_geometry(g.x, g.y, g.w, g.h)
  if g.x == 0 then
    if LEFT_EDGE_CORRECTION == "pos1" then
      set_window_position(g.x, g.y)
    elseif LEFT_EDGE_CORRECTION == "pos2" then
      set_window_position2(g.x, g.y)
    end
  end

  -- debug_print(string.format("geometry: %s/%s -> %dx%d+%d+%d", tostring(domain), cls, g.w, g.h, g.x, g.y))
end
