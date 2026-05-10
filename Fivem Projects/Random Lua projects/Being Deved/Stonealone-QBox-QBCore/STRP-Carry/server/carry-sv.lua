local carryCooldowns = {}
local carryCooldown = 5 -- seconds

local function getClosestPlayer(src)
    local players = GetPlayers()
    local closest = nil
    local closestDist = 3.0 -- max distance

    local srcPed = GetPlayerPed(src)
    local srcCoords = GetEntityCoords(srcPed)

    for _, id in ipairs(players) do
        id = tonumber(id)
        if id ~= src then
            local ped = GetPlayerPed(id)
            local coords = GetEntityCoords(ped)
            local dist = #(srcCoords - coords)

            if dist < closestDist then
                closest = id
                closestDist = dist
            end
        end
    end

    return closest
end

RegisterNetEvent("carry:request")
AddEventHandler("carry:request", function()
    local src = source
    local now = os.time()

    if carryCooldowns[src] and now - carryCooldowns[src] < carryCooldown then
        local remaining = carryCooldown - (now - carryCooldowns[src])
        TriggerClientEvent("chat:addMessage", src, {
            args = {"Carry", "You must wait " .. remaining .. "s before using /carry again."}
        })
        return
    end

    carryCooldowns[src] = now

    local target = getClosestPlayer(src)

    if target then
        TriggerClientEvent("carry:start", src, GetPlayerServerId(target))
        TriggerClientEvent("carry:start", target, GetPlayerServerId(src))
    else
        TriggerClientEvent("chat:addMessage", src, {
            args = {"Carry", "No player nearby."}
        })
    end
end)


RegisterNetEvent("carry:stop")
AddEventHandler("carry:stop", function()
    local src = source

    -- Stop for both players
    TriggerClientEvent("carry:stop", src)

    -- Also stop for anyone carrying them
    local players = GetPlayers()
    for _, id in ipairs(players) do
        TriggerClientEvent("carry:stop", tonumber(id))
    end
end)
