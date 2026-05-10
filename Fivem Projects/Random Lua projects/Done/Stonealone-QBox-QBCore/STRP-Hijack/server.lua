local QBCore = exports['qb-core']:GetCoreObject()
local hijackCooldowns = {}

local Config = {
    HijackAlertChance = 1.85,
    HijackCooldown = 5000,
    MaxHijackDistance = 10.0,

    -- Developer mode: enable this when testing dispatch behavior while on duty.
    DevMode = true,
    DevForceDispatch = true,
}

local function getPlayerId(src)
    return GetPlayerIdentifier(src, 0) or 'unknown'
end

local function hasHijackCooldown(src)
    local playerId = getPlayerId(src)
    if hijackCooldowns[playerId] and GetGameTimer() - hijackCooldowns[playerId] < Config.HijackCooldown then
        return true
    end
    return false
end

local function setHijackCooldown(src)
    local playerId = getPlayerId(src)
    hijackCooldowns[playerId] = GetGameTimer()
end

local function broadcastDispatchAlert(plate, coords)
    local alertChance = Config.HijackAlertChance
    if Config.DevMode and Config.DevForceDispatch then
        alertChance = 1.0
    end

    if alertChance and math.random() <= alertChance then
        local alertSent = false

        if exports['cd_dispatch'] then
            local ok = pcall(function()
                exports['cd_dispatch']:SendAlert({
                    coords = coords,
                    title = 'Vehicle Hijack',
                    description = 'A vehicle with plate ' .. plate .. ' has been hijacked.',
                    isImportant = true,
                    flash = true,
                    color = 1,
                    scale = 1.0,
                })
            end)

            alertSent = ok
        end

        if not alertSent then
            TriggerEvent('chat:addMessage', {
                args = { 'DISPATCH', 'Vehicle hijack reported - Plate: ' .. plate },
                color = { 255, 0, 0 }
            })
        end
    end
end

local function serverNotify(src, data)
    if not src or not data or not data.description then
        return
    end

    local sent = pcall(function()
        TriggerClientEvent('ox_lib:notify', src, data)
    end)

    if not sent then
        TriggerClientEvent('chat:addMessage', src, {
            args = { 'HIJACK', data.description },
            color = data.type == 'error' and { 255, 0, 0 } or { 0, 255, 0 }
        })
    end
end

local function tryGiveVehicleKeys(src, plate)
    if not plate or plate == '' then
        return false
    end

    local function tryCalls(calls)
        for _, fn in ipairs(calls) do
            if pcall(fn) then
                return true
            end
        end
        return false
    end

    if exports['qb-vehiclekeys'] and type(exports['qb-vehiclekeys'].GiveKeys) == 'function' then
        return tryCalls({
            function() exports['qb-vehiclekeys']:GiveKeys(src, plate, 0, 0, true) end,
            function() exports['qb-vehiclekeys']:GiveKeys(src, plate, true) end,
            function() exports['qb-vehiclekeys']:GiveKeys(plate, src) end,
            function() exports['qb-vehiclekeys']:GiveKeys(GetPlayerName(src), plate, 0, 0, true) end,
        })
    end

    return tryCalls({
        function() TriggerEvent('qb-vehiclekeys:server:AcquireVehicleKeys', plate, src) end,
        function() TriggerEvent('qb-vehiclekeys:server:AcquireVehicleKeys', src, plate) end,
        function() TriggerEvent('qb-vehiclekeys:server:AcquireVehicleKeys', plate, GetPlayerName(src)) end,
        function() TriggerEvent('qb-vehiclekeys:server:AcquireVehicleKeys', GetPlayerName(src), plate) end,
    })
end

RegisterNetEvent('hijack:server:AttemptHijack', function(vehicleNetId, plate, coords)
    local src = source
    local player = QBCore.Functions.GetPlayer(src)

    if not player then
        serverNotify(src, {
            type = 'error',
            description = 'Player data not found.',
        })
        return
    end

    if hasHijackCooldown(src) then
        serverNotify(src, {
            type = 'error',
            description = 'You are on hijack cooldown.',
        })
        return
    end

    if type(plate) ~= 'string' or plate == '' then
        serverNotify(src, {
            type = 'error',
            description = 'Invalid vehicle plate.',
        })
        return
    end

    if type(coords) ~= 'vector3' and not (type(coords) == 'table' and coords.x and coords.y and coords.z) then
        serverNotify(src, {
            type = 'error',
            description = 'Invalid coordinates.',
        })
        return
    end

    setHijackCooldown(src)

    local gaveKeys = tryGiveVehicleKeys(src, plate)
    if not gaveKeys then
        serverNotify(src, {
            type = 'warning',
            description = 'Hijacked vehicle, but key assignment failed. Check qb-vehiclekeys compatibility.',
        })
    end

    serverNotify(src, {
        type = 'success',
        description = 'Vehicle successfully hijacked.',
    })

    pcall(function()
        TriggerEvent('qb-log:server:CreateLog', 'hijack', 'Hijack', 'green', 'Player ' .. GetPlayerName(src) .. ' hijacked a vehicle with plate ' .. plate)
    end)

    broadcastDispatchAlert(plate, coords)
end)

AddEventHandler('onPlayerDropped', function()
    local playerId = getPlayerId(source)
    if hijackCooldowns[playerId] then
        hijackCooldowns[playerId] = nil
    end
end)
