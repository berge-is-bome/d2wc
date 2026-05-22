-- Only act on real app windows
if (get_window_type() ~= "WINDOW_TYPE_NORMAL") then
  return
end

-- Workspace by Qubes domain
local workspaceAssociation = {
  ["dom0"] = 1,
  ["personal"] = 1,
  ["test"] = 4,
  ["business"] = 2,
  ["business-clients"] = 2,
  ["customer"] = 3,
}

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

-- Assign workspace only if we have a domain
if domain then
  local ws = workspaceAssociation[domain]
  if ws and ws > 0 and ws <= get_workspace_count() then
    set_window_workspace(ws)
  end
end

-- Class helper: get WM_CLASS class part in lowercase (after the last colon)
local function get_lower_class()
  local s = (get_class_instance_name() or ""):lower()
  return s:match(".*:([^:]+)$") or s
end

local cls = get_lower_class()

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
  nav_wide     = { x = 100,  y = 456,  w = 3624, h = 1389 },
  centered_mid = { x = 960,  y = 540,  w = 1200, h = 900  },
  code_right   = { x = 2200, y = 120,  w = 1600, h = 1400 },
  half_right   = { x = 1913, y = 0,    w = 1920, h = 2115 },
  half_left    = { x = 7,    y = 0,    w = 1920, h = 2115 },
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
      nav_wide   = { "krusader" }, -- shared geometry
   -- nav_wide   = { "krusader", "okular" },  -- shared geometry
      half_right = { "okular" }, -- shared geometry
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

-- Resolve geometry for domain+class, then fall back to global defaults

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

-- Apply geometry if a rule matched
local g = find_geometry(domain, cls)
if g then
  set_window_geometry(g.x, g.y, g.w, g.h)
  -- debug_print(string.format("geometry: %s/%s -> %dx%d+%d+%d", tostring(domain), cls, g.w, g.h, g.x, g.y))
end
