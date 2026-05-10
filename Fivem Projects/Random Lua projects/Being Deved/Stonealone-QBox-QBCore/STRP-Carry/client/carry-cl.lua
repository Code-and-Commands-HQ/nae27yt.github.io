local carrying = false
local targetped = nil
local lastCarryTime = 0
local carryCooldown = 5 -- seconds

-- Annimation
local function playAnim(dict, anim)
    RequestAnimDict(dict)
    while not HasAnimDictLoaded(dict) do
        Citizen.Wait(100)
    end
    TaskPlayAnim(PlayerPedId(), dict, anim, 8.0, -8.0, -1, 50, 0, false, false, false)
end

--attach logic
local function attachToTarget(target)
    local playerPed = PlayerPedId()
    local targetCoords = GetEntityCoords(target)
    AttachEntityToEntity(playerPed, target, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 180.0, false, false, false, false, 2, true)
     if DoesEntityExist(target) then
        carrying = true
        playAnim("missfinale_c2mcs_1", "fin_c2_mcs_1_camman")
        
        AttachEntityToEntity(
            playerPed,
            targetped,
            11816, -- bone index (spine)
            0.27, 0.15, 0.0, -- position offset
            0.5, 0.5, 180.0, -- rotation
            false, false, false, false, 2, true
        )
    end
end
-- Detach logic
local function detachFromTarget()
    local playerPed = PlayerPedId()
    carrying = false
    DetachEntity(playerPed, true, false)
    ClearPedTasks(playerPed)
end
-- Receive server approval
RegisterNetEvent("carry:start")
AddEventHandler("carry:start", function(target)
    attachToTarget(target)
end)

-- Receive stop event
RegisterNetEvent("carry:stop")
AddEventHandler("carry:stop", function()
    detachFromTarget()
end)

-- Command
RegisterCommand("carry", function()
    local now = GetGameTimer() / 1000

    if now - lastCarryTime < carryCooldown then
        local remaining = math.floor(carryCooldown - (now - lastCarryTime))
        TriggerEvent("chat:addMessage", { args = {"Carry", "Please wait " .. remaining .. "s before using /carry again."}})
        return
    end

    lastCarryTime = now

    if carrying then
        TriggerServerEvent("carry:stop")
    else
        TriggerServerEvent("carry:request")
    end
end)
