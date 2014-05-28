from direct.directnotify.DirectNotifyGlobal import *
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from pandac.PandaModules import *
from toontown.building import DistributedDoorAI
from toontown.building import DoorTypes, FADoorCodes
from toontown.building.DistributedHQInteriorAI import DistributedHQInteriorAI
from toontown.building.DistributedTutorialInteriorAI import DistributedTutorialInteriorAI
from toontown.suit import DistributedTutorialSuitAI
from toontown.suit import SuitDNA
from toontown.toon import NPCToons
from toontown.toon import ToonDNA
from toontown.toon.DistributedNPCSpecialQuestGiverAI import DistributedNPCSpecialQuestGiverAI
from toontown.toonbase import ToontownGlobals


class TutorialManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('TutorialManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.zoneAllocator = self.air.zoneAllocator

        self.currentAllocatedZones = {}

    def requestTutorial(self):
        avId = self.air.getAvatarIdFromSender()

        print 'tutorial request from AvatarId: %s'%(avId)
        zones = self.createTutorial()
        self.enterTutorial(avId, ToontownGlobals.Tutorial, zones[0], zones[1],
                           zones[2])

    def rejectTutorial(self):
        #I have no idea what this is for...
        print 'tutorial reject'

    def requestSkipTutorial(self):
        avId = self.air.getAvatarIdFromSender()
        self.skipTutorialResponse(avId, 1)

    def skipTutorialResponse(self, avId, allOk):
        self.sendUpdateToAvatarId(avId, 'skipTutorialResponse', [allOk])

    def enterTutorial(self, avId, branchZone, streetZone, shopZone, hqZone):
        self.currentAllocatedZones[avId] = (streetZone, shopZone, hqZone)
        self.sendUpdateToAvatarId(avId, 'enterTutorial',
                                  [branchZone, streetZone, shopZone, hqZone])

    def createTutorial(self):
        streetZone = self.zoneAllocator.allocate()
        shopZone = self.zoneAllocator.allocate()
        hqZone = self.zoneAllocator.allocate()

        self.createShop(streetZone, shopZone, hqZone)
        self.createHQ(streetZone, shopZone, hqZone)
        self.createStreet(streetZone, shopZone, hqZone)

        return (streetZone, shopZone, hqZone)

    def createShop(self, streetZone, shopZone, hqZone):
        shopInterior = DistributedTutorialInteriorAI(2, self.air, shopZone)

        desc = NPCToons.NPCToonDict.get(20000)
        npc = NPCToons.createNPC(self.air, 20000, desc, shopZone)
        npc.setTutorial(1)
        shopInterior.setTutorialNpcId(npc.doId)
        shopInterior.generateWithRequired(shopZone)

        extShopDoor = DistributedDoorAI.DistributedDoorAI(self.air, 2, DoorTypes.EXT_STANDARD,
                                        lockValue=FADoorCodes.DEFEAT_FLUNKY_TOM)
        intShopDoor = DistributedDoorAI.DistributedDoorAI(self.air, 2, DoorTypes.INT_STANDARD,
                                        lockValue=FADoorCodes.TALK_TO_TOM)
        extShopDoor.setOtherDoor(intShopDoor)
        intShopDoor.setOtherDoor(extShopDoor)
        extShopDoor.zoneId = streetZone
        intShopDoor.zoneId = shopZone
        extShopDoor.generateWithRequired(streetZone)
        extShopDoor.sendUpdate('setDoorIndex', [extShopDoor.getDoorIndex()])
        intShopDoor.generateWithRequired(shopZone)
        intShopDoor.sendUpdate('setDoorIndex', [intShopDoor.getDoorIndex()])

        self.accept('intShopDoor-{0}'.format(shopZone), intShopDoor.setDoorLock)
        self.accept('extShopDoor-{0}'.format(streetZone), extShopDoor.setDoorLock)

    def createHQ(self, streetZone, shopZone, hqZone):
        interior = DistributedHQInteriorAI(1, self.air, hqZone)
        interior.generateWithRequired(hqZone)
        interior.setTutorial(1)

        desc = NPCToons.NPCToonDict.get(20002)
        npc = NPCToons.createNPC(self.air, 20002, desc, hqZone)
        npc.setTutorial(1)
        npc.setHq(1)

        door0 = DistributedDoorAI.DistributedDoorAI(
            self.air, 1, DoorTypes.EXT_HQ, doorIndex=0,
            lockValue=FADoorCodes.DEFEAT_FLUNKY_HQ)
        door1 = DistributedDoorAI.DistributedDoorAI(
            self.air, 1, DoorTypes.EXT_HQ, doorIndex=1,
            lockValue=FADoorCodes.DEFEAT_FLUNKY_HQ)
        insideDoor0 = DistributedDoorAI.DistributedDoorAI(
            self.air, 1, DoorTypes.INT_HQ, doorIndex=0,
            lockValue=FADoorCodes.TALK_TO_HQ)
        insideDoor1 = DistributedDoorAI.DistributedDoorAI(
            self.air, 1, DoorTypes.INT_HQ, doorIndex=1,
            lockValue=FADoorCodes.TALK_TO_HQ)
        door0.setOtherDoor(insideDoor0)
        insideDoor0.setOtherDoor(door0)
        door1.setOtherDoor(insideDoor1)
        insideDoor1.setOtherDoor(door1)
        door0.zoneId = streetZone
        door1.zoneId = streetZone
        insideDoor0.zoneId = hqZone
        insideDoor1.zoneId = hqZone
        door0.generateWithRequired(streetZone)
        door1.generateWithRequired(streetZone)
        door0.sendUpdate('setDoorIndex', [door0.getDoorIndex()])
        door1.sendUpdate('setDoorIndex', [door1.getDoorIndex()])
        insideDoor0.generateWithRequired(hqZone)
        insideDoor1.generateWithRequired(hqZone)
        insideDoor0.sendUpdate('setDoorIndex', [insideDoor0.getDoorIndex()])
        insideDoor1.sendUpdate('setDoorIndex', [insideDoor1.getDoorIndex()])

        self.accept('extHqDoor0-{0}'.format(streetZone), door0.setDoorLock)
        self.accept('extHqDoor1-{0}'.format(streetZone), door1.setDoorLock)
        self.accept('intHqDoor0-{0}'.format(hqZone), insideDoor0.setDoorLock)
        self.accept('intHqDoor1-{0}'.format(hqZone), insideDoor1.setDoorLock)

    def createStreet(self, streetZone, shopZone, hqZone):
        flunky = DistributedTutorialSuitAI.DistributedTutorialSuitAI(self.air)
        suitType = SuitDNA.getSuitType('f')
        suitTrack = SuitDNA.getSuitDept('f')
        flunky.setupSuitDNA(1, suitType, suitTrack)
        flunky.generateWithRequired(streetZone)

    def allDone(self):
        avId = self.air.getAvatarIdFromSender()

        #Deallocate zones the Avatar took.
        for zoneId in self.currentAllocatedZones[avId]:
            self.zoneAllocator.free(zoneId)

    def toonArrived(self):
        avId = self.air.getAvatarIdFromSender()

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.b_setTutorialAck(1)
