local HIJACK_DISTANCE = 5.0
local hijacking = false
local oxTargetVehicles = {}
local QBCore = exports['qb-core']:GetCoreObject()
local lib = rawget(_G, 'lib')

local function notify(text)
    SetNotificationTextEntry('STRING')
    AddTextComponentString(text)
    DrawNotification(false, false)
end

local function oxLibNotify(message)
    if exports.ox_lib and type(exports.ox_lib.notify) == 'function' then
        exports.ox_lib:notify({
            type = 'success',
            description = message,
        })
    else
        notify(message)
    end
end

local function playLockpickAnimation()
    local playerPed = PlayerPedId()
    RequestAnimDict('veh_drug_play')
    while not HasAnimDictLoaded('veh_drug_play') do
        Wait(0)
    end
    TaskPlayAnim(playerPed, 'veh_drug_play', 'veh_drug_use', 8.0, -8.0, -1, 1, 0, false, false, false)
end

local function stopLockpickAnimation()
    local playerPed = PlayerPedId()
    StopAnimTask(playerPed, 'veh_drug_play', 'veh_drug_use', 1.0)
    RemoveAnimDict('veh_drug_play')
end

local function runLockpickGame()
    local playerPed = PlayerPedId()
    
    -- Play lockpicking animation
    playLockpickAnimation()
    
    if exports.ox_lib and type(exports.ox_lib.minigame) == 'function' then
        local result = exports.ox_lib:minigame('lockpick', {
            difficulty = 1,
        })
        stopLockpickAnimation()
        return result
    end
    
    -- Fallback if ox_lib not available
    stopLockpickAnimation()
    return true
end

local function isVehicleValidForTarget(vehicle)
    if not DoesEntityExist(vehicle) then
        return false
    end

    if not IsVehicleDriveable(vehicle, false) then
        return false
    end

    local driver = GetPedInVehicleSeat(vehicle, -1)
    if DoesEntityExist(driver) and IsPedAPlayer(driver) then
        return false
    end

    return true
end

local function waitForDriverExit(driver, vehicle, timeout)
    local start = GetGameTimer()
    while GetGameTimer() - start < timeout do
        if not IsPedInVehicle(driver, vehicle, true) then
            return true
        end
        Wait(50)
    end
    return false
end

local function clearTarget(vehicle)
    if not oxTargetVehicles[vehicle] then
        return
    end

    if exports.ox_target and type(exports.ox_target.removeLocalEntity) == 'function' then
        exports.ox_target:removeLocalEntity(vehicle)
    end

    oxTargetVehicles[vehicle] = nil
end

local function registerTarget(vehicle)
    if not DoesEntityExist(vehicle) or oxTargetVehicles[vehicle] then
        return
    end

    if not exports.ox_target or type(exports.ox_target.addLocalEntity) ~= 'function' then
        return
    end

    exports.ox_target:addLocalEntity(vehicle, {
        {
            name = 'hijack_vehicle',
            icon = 'fa-solid fa-car-burst',
            label = 'Hijack vehicle',
            distance = HIJACK_DISTANCE,
            onSelect = function(entity)
                if hijacking then
                    oxLibNotify('Already hijacking a vehicle.')
                    return
                end

                if type(entity) == 'table' and entity.entity then
                    entity = entity.entity
                end

                if type(entity) ~= 'number' or not DoesEntityExist(entity) then
                    oxLibNotify('Invalid vehicle target.')
                    return
                end

                local playerPed = PlayerPedId()
                if IsPedInAnyVehicle(playerPed, false) then
                   oxLibNotify('Leave your vehicle first.')
                    return
                end

                local driver = GetPedInVehicleSeat(entity, -1)
                if DoesEntityExist(driver) and IsPedAPlayer(driver) then
                    oxLibNotify('Cannot hijack a player-driven vehicle.')
                    return
                end

                hijacking = true
                if not runLockpickGame() then
                    oxLibNotify('Lockpicking failed.')
                    hijacking = false
                    return
                end

                if DoesEntityExist(driver) and not IsPedDeadOrDying(driver, true) then
                    SetVehicleDoorsLocked(entity, 1)
                    SetEntityAsMissionEntity(entity, true, true)
                    ClearPedTasks(driver)
                    TaskLeaveVehicle(driver, entity, 0)
                    Wait(750)
                    if not waitForDriverExit(driver, entity, 3000) then
                        ClearPedTasksImmediately(driver)
                        Wait(250)
                    end
                    Wait(250)
                end

                local plate = QBCore.Functions.GetPlate(entity)
                if plate and type(plate) == 'string' and plate ~= '' then
                    local coords = GetEntityCoords(entity)
                    TriggerServerEvent('hijack:server:AttemptHijack', NetworkGetNetworkIdFromEntity(entity), plate, coords)
                    SetVehicleDoorsLocked(entity, 1)
                else
                    oxLibNotify('Unable to retrieve vehicle plate.')
                end

                hijacking = false
            end,
        },
    })

    oxTargetVehicles[vehicle] = true
end

local function updateTargets()
    if not exports.ox_target or type(exports.ox_target.addLocalEntity) ~= 'function' then
        return
    end

    local playerCoords = GetEntityCoords(PlayerPedId())
    for _, vehicle in ipairs(GetGamePool('CVehicle')) do
        if DoesEntityExist(vehicle) then
            local vehicleCoords = GetEntityCoords(vehicle)
            if #(playerCoords - vehicleCoords) <= 30.0 and isVehicleValidForTarget(vehicle) then
                registerTarget(vehicle)
            else
                clearTarget(vehicle)
            end
        end
    end
end

Citizen.CreateThread(function()
    while true do
        updateTargets()
        Wait(1500)
    end
end)

AddEventHandler('onResourceStop', function(resourceName)
    if resourceName ~= GetCurrentResourceName() then
        return
    end

    for vehicle in pairs(oxTargetVehicles) do
        clearTarget(vehicle)
    end
end)
