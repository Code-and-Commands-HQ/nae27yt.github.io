CreateThread(function()
    while true do
        local ped = PlayerPedId()
        local heading = GetEntityHeading(ped)

        local coords = GetEntityCoords(ped)
        local streetHash = GetStreetNameAtCoord(coords.x, coords.y, coords.z)
        local streetName = GetStreetNameFromHashKey(streetHash)

        SendNUIMessage({
            action = "updateCompass",
            heading = heading,
            street = streetName
        })

        Wait(100) -- smooth but not heavy
    end
end)
