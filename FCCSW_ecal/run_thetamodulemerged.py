#
# IMPORTS
#
from Configurables import ApplicationMgr
from Configurables import EventCounter
from Configurables import AuditorSvc, ChronoAuditor
# Event generation
from Configurables import GenAlg
# G4 simulation
from Configurables import SimG4Alg
from Configurables import SimG4PrimariesFromEdmTool
from Configurables import SimG4SaveCalHits
from Configurables import SimG4ConstantMagneticFieldTool
from Configurables import SimG4Svc
from Configurables import SimG4FullSimActions
from Configurables import SimG4SaveParticleHistory
# Geometry
from Configurables import GeoSvc
# Input/output
from Configurables import FCCDataSvc
from Configurables import PodioOutput
from Configurables import HepMCToEDMConverter
# Create cells
from Configurables import CreateCaloCells
from Configurables import CreateEmptyCaloCellsCollection
# Cell positioning tools
from Configurables import CreateCaloCellPositionsFCCee
from Configurables import CellPositionsECalBarrelModuleThetaSegTool
# Redo segmentation for ECAL and HCAL
from Configurables import RedoSegmentation
# Read noise values from file and generate noise in cells
from Configurables import NoiseCaloCellsVsThetaFromFileTool
# Apply sampling fraction corrections
from Configurables import CalibrateCaloHitsTool
from Configurables import CalibrateInLayersTool
# Up/down stream correction
from Configurables import CorrectCaloClusters
# SW clustering
from Configurables import CaloTowerToolFCCee
from Configurables import CreateCaloClustersSlidingWindowFCCee
# Topo clustering
from Configurables import CaloTopoClusterInputTool
from Configurables import TopoCaloNeighbours
from Configurables import TopoCaloNoisyCells
from Configurables import CaloTopoClusterFCCee
# Decorate clusters with shower shape parameters
from Configurables import AugmentClustersFCCee
# MVA calibration
from Configurables import CalibrateCaloClusters
# Logger
from Gaudi.Configuration import INFO, VERBOSE, DEBUG
# Units and physical constants
from GaudiKernel.SystemOfUnits import GeV, tesla, mm
from GaudiKernel.PhysicalConstants import pi, halfpi, twopi
# python libraries
import os
from math import cos, sin, tan
#
# SETTINGS
#

# - general settings
#
use_pythia = False  # use pythia or particle gun
addNoise = True     # add noise or not to the cell energy
dumpGDML = False    # create GDML file of detector model
runHCal = False     # simulate only the ECAL or both ECAL+HCAL

# - what to save in output file
#
# for big productions, save significant space removing hits and cells
# however, hits and cluster cells might be wanted for small productions for detailed event displays
# also, cluster cells are needed for the MVA training
saveHits = True
saveCells = True
saveClusterCells = True

# - clustering
#
doSWClustering = True
doTopoClustering = True

# cluster energy corrections
# simple parametrisations of up/downstream losses
# not to be applied for ECAL+HCAL clustering
applyUpDownstreamCorrections = True and not runHCal

# BDT regression from total cluster energy and fraction of energy in each layer (after correction for sampling fraction)
# not to be applied for ECAL+HCAL clustering (MVA trained only on ECAL)
applyMVAClusterEnergyCalibration = False and not runHCal

# calculate cluster energy and barycenter per layer and save it as extra parameters
addShapeParameters = True and not runHCal

# - input for simulations (momentum is expected in GeV!)
#

# Parameters for the particle gun simulations, dummy if use_pythia is set
# to True
# theta from 80 to 100 degrees corresponds to -0.17 < eta < 0.17
# reminder: cell granularity in theta = 0.5625 degrees
# (in strips: 0.5625/4=0.14)

# number of events to simulate
# Nevts = 20000
Nevts = 10
# Nevts = 1
# Nevts=1000

# particle momentum and direction
# momentum = 100  # in GeV
momentum = 50  # in GeV
# momentum = 10  # in GeV
thetaMin = 45  # degrees
thetaMax = 135  # degrees
# thetaMin = 89
# thetaMax = 91
# thetaMin = 90  # degrees
# thetaMax = 90  # degrees
# phiMin = halfpi
# phiMax = halfpi
phiMin = 0
phiMax = twopi

# particle origin
# origR = 1000.0*mm
origR = 0.0 * mm
origTheta = halfpi
origPhi = 0.0

# particle type: 11 electron, 13 muon, 22 photon, 111 pi0, 211 pi+
# pdgCode = 11
pdgCode = 22
# pdgCode = 111
# pdgCode = 211

# Set to true if history from Geant4 decays is needed (e.g. to get the
# photons from pi0)
saveG4Hist = False
if (pdgCode == 111):
    saveG4Hist = True

# turn on/off B field
magneticField = False


#
# ALGORITHMS AND SERVICES SETUP
#

podioevent = FCCDataSvc("EventDataSvc")

# Particle gun setup
genAlg = GenAlg()
if use_pythia:
    from Configurables import PythiaInterface
    pythia8gentool = PythiaInterface()
    pythia8gentool.pythiacard = os.path.join(
        os.environ.get('PWD', ''),
        "MCGeneration/ee_Zgamma_inclusive.cmd"
    )
    # pythia8gentool.pythiacard = "MCGeneration/ee_Z_ee.cmd"
    pythia8gentool.printPythiaStatistics = False
    pythia8gentool.pythiaExtraSettings = [""]
    genAlg.SignalProvider = pythia8gentool
else:
    from Configurables import MomentumRangeParticleGun
    pgun = MomentumRangeParticleGun("ParticleGun")
    pgun.PdgCodes = [pdgCode]
    pgun.MomentumMin = momentum * GeV
    pgun.MomentumMax = momentum * GeV
    pgun.PhiMin = phiMin
    pgun.PhiMax = phiMax
    pgun.ThetaMin = thetaMin * pi / 180.
    pgun.ThetaMax = thetaMax * pi / 180.
    genAlg.SignalProvider = pgun

genAlg.hepmc.Path = "hepmc"

# smear/shift vertex
if origR > 0.0:
    origX = origR * cos(origPhi)
    origY = origR * sin(origPhi)
    origZ = origR / tan(origTheta)
    print("Particle gun will be moved to %f %f %f" % (origX, origY, origZ))
    from Configurables import GaussSmearVertex
    vertexSmearAndShiftTool = GaussSmearVertex()
    vertexSmearAndShiftTool.xVertexSigma = 0.
    vertexSmearAndShiftTool.yVertexSigma = 0.
    vertexSmearAndShiftTool.tVertexSigma = 0.
    vertexSmearAndShiftTool.xVertexMean = origX
    vertexSmearAndShiftTool.yVertexMean = origY
    vertexSmearAndShiftTool.zVertexMean = origZ
    vertexSmearAndShiftTool.tVertexMean = 0.
    genAlg.VertexSmearingTool = vertexSmearAndShiftTool

# hepMC -> EDM converter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
genParticlesOutputName = "genParticles"
hepmc_converter.GenParticles.Path = genParticlesOutputName
hepmc_converter.hepmcStatusList = []
hepmc_converter.OutputLevel = INFO

# Simulation setup
# Detector geometry
geoservice = GeoSvc("GeoSvc")
# if K4GEO is empty, this should use relative path to working directory
path_to_detector = os.environ.get("K4GEO", "")
print(path_to_detector)
detectors_to_use = [
    'FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml'
]
# prefix all xmls with path_to_detector
geoservice.detectors = [
    os.path.join(path_to_detector, _det) for _det in detectors_to_use
]
geoservice.OutputLevel = INFO

# Geant4 service
# Configures the Geant simulation: geometry, physics list and user actions
actions = SimG4FullSimActions()
if saveG4Hist:
    actions.enableHistory = True
    actions.energyCut = 1.0 * GeV
    saveHistTool = SimG4SaveParticleHistory("saveHistory")

geantservice = SimG4Svc(
    "SimG4Svc",
    detector='SimG4DD4hepDetector',
    physicslist="SimG4FtfpBert",
    actions=actions
)

# write GDML with detector model
if dumpGDML:
    from Configurables import GeoToGdmlDumpSvc
    gdmldumpservice = GeoToGdmlDumpSvc("GeoToGdmlDumpSvc")

# Fixed seed to have reproducible results, change it for each job if you
# split one production into several jobs
# Mind that if you leave Gaudi handle random seed and some job start within
# the same second (very likely) you will have duplicates
geantservice.randomNumbersFromGaudi = False
geantservice.seedValue = 4242

# Range cut
geantservice.g4PreInitCommands += ["/run/setCut 0.1 mm"]

# Set magnetic field
if magneticField == 1:
    field = SimG4ConstantMagneticFieldTool(
        "SimG4ConstantMagneticFieldTool",
        FieldComponentZ=-2 * tesla,
        FieldOn=True,
        IntegratorStepper="ClassicalRK4"
    )
else:
    field = SimG4ConstantMagneticFieldTool(
        "SimG4ConstantMagneticFieldTool",
        FieldOn=False
    )

# Geant4 algorithm
# Translates EDM to G4Event, passes the event to G4, writes out outputs
# via tools and a tool that saves the calorimeter hits

# Detector readouts
# ECAL
ecalBarrelReadoutName = "ECalBarrelModuleThetaMerged"  # barrel, original segmentation (baseline)
ecalBarrelReadoutName2 = "ECalBarrelModuleThetaMerged2"  # barrel, after re-segmentation (for optimisation studies)
ecalEndcapReadoutName = "ECalEndcapTurbine"  # endcap, turbine-like (baseline)
# HCAL
if runHCal:
    hcalBarrelReadoutName = "HCalBarrelReadout"  # barrel, layer-row-theta-phi based (can be used to fill various cell collections with different readouts)
    hcalBarrelReadoutName2 = "BarHCal_Readout_phitheta"  # barrel, layer-theta-phi based, groups tiles from different rows together (baseline)
    hcalEndcapReadoutName = "HCalEndcapReadout"  # endcap
else:
    hcalBarrelReadoutName = ""
    hcalBarrelReadoutName2 = ""
    hcalEndcapReadoutName = ""

# Configure saving of calorimeter positioned hits
# - ECAL barrel
ecalBarrelHitsName = "ECalBarrelPositionedHits"
saveECalBarrelTool = SimG4SaveCalHits(
    "saveECalBarrelHits",
    readoutName=ecalBarrelReadoutName,
    OutputLevel=INFO
)
saveECalBarrelTool.CaloHits.Path = ecalBarrelHitsName

# - ECAL encap
saveECalEndcapTool = SimG4SaveCalHits(
    "saveECalEndcapHits",
    readoutName=ecalEndcapReadoutName,
    OutputLevel=INFO
)
saveECalEndcapTool.CaloHits.Path = "ECalEndcapHits"

if runHCal:
    # - HCAL barrel
    hcalBarrelHitsName = "HCalBarrelPositionedHits"
    saveHCalTool = SimG4SaveCalHits(
        "saveHCalBarrelHits",
        readoutName=hcalBarrelReadoutName,
        OutputLevel=INFO
    )
    saveHCalTool.CaloHits.Path = hcalBarrelHitsName

    # - HCAL endcap
    # saveHCalEndcapTool = SimG4SaveCalHits(
    #    "saveHCalEndcapHits",
    #    readoutName = hcalEndcapReadoutName
    # )
    # saveHCalEndcapTool.CaloHits.Path = "HCalEndcapHits"

# next, create the G4 algorithm, giving the list of names of tools ("XX/YY")
particle_converter = SimG4PrimariesFromEdmTool("EdmConverter")
particle_converter.GenParticles.Path = genParticlesOutputName

outputTools = [
    saveECalBarrelTool,
    saveECalEndcapTool
]
if runHCal:
    outputTools += [
        saveHCalTool,
        # saveHCalEndcapTool
    ]

if saveG4Hist:
    outputTools += [saveHistTool]

geantsim = SimG4Alg("SimG4Alg",
                    outputs=outputTools,
                    eventProvider=particle_converter,
                    OutputLevel=INFO)

# Digitization (Merging hits into cells, EM scale calibration)
# EM scale calibration (sampling fraction)
# - ECAL barrel
calibEcalBarrel = CalibrateInLayersTool("CalibrateECalBarrel",
                                        samplingFraction=[0.3775596654349802] * 1 + [0.13400227700041234] * 1 + [0.14390509963164044] * 1 + [0.14998482026270935] * 1 + [0.15457673722531148] * 1 + [0.15928098152159675] * 1 + [0.1635367867767212] * 1 + [0.16801070646031507] * 1 + [0.1713409944779989] * 1 + [0.17580195406064622] * 1 + [0.17966699467772812] * 1,
                                        readoutName=ecalBarrelReadoutName,
                                        layerFieldName="layer")

# - ECAL endcap (TO BE UPDATED)
calibEcalEndcap = CalibrateCaloHitsTool(
    "CalibrateECalEndcap", invSamplingFraction="4.27")

if runHCal:
    # - HCAL barrel
    calibHcells = CalibrateCaloHitsTool(
        "CalibrateHCal", invSamplingFraction="31.4")
    # - HCAL endcap
    calibHcalEndcap = CalibrateCaloHitsTool(
        "CalibrateHCalEndcap", invSamplingFraction="31.7")

# Create cells in ECal barrel
# 1. step - merge hits into cells with theta and module segmentation
# (module is a 'physical' cell i.e. lead + LAr + PCB + LAr +lead)
# 2. step - rewrite the cellId using the merged theta-module segmentation
# (merging several modules and severla theta readout cells).
# Add noise at this step if you derived the noise already assuming merged cells

# Step 1: merge hits into cells according to initial segmentation
ecalBarrelCellsName = "ECalBarrelCells"
if not addNoise:
    createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCells",
                                        doCellCalibration=True,
                                        calibTool=calibEcalBarrel,
                                        addCellNoise=False,
                                        filterCellNoise=False,
                                        addPosition=True,
                                        OutputLevel=INFO,
                                        hits=ecalBarrelHitsName,
                                        cells=ecalBarrelCellsName)

# Step 2a: compute new cellID of cells based on new readout
# (merged module-theta segmentation with variable merging vs layer)
resegmentEcalBarrel = RedoSegmentation("ReSegmentationEcal",
                                       # old bitfield (readout)
                                       oldReadoutName=ecalBarrelReadoutName,
                                       # specify which fields are going to be altered (deleted/rewritten)
                                       oldSegmentationIds=["module", "theta"],
                                       # new bitfield (readout), with new segmentation (merged modules and theta cells)
                                       newReadoutName=ecalBarrelReadoutName2,
                                       OutputLevel=INFO,
                                       debugPrint=200,
                                       inhits=ecalBarrelCellsName,
                                       outhits="ECalBarrelCellsMerged")

# Step 2b: merge new cells with same cellID together
# do not apply cell calibration again since cells were already
# calibrated in Step 1
ecalBarrelCellsName2 = "ECalBarrelCells2"
createEcalBarrelCells2 = CreateCaloCells("CreateECalBarrelCells2",
                                         doCellCalibration=False,
                                         addCellNoise=False,
                                         filterCellNoise=False,
                                         OutputLevel=INFO,
                                         hits="ECalBarrelCellsMerged",
                                         cells=ecalBarrelCellsName2)

# Add to Ecal barrel cells the position information
# (good for physics, all coordinates set properly)
cellPositionEcalBarrelTool = CellPositionsECalBarrelModuleThetaSegTool(
    "CellPositionsECalBarrel",
    readoutName=ecalBarrelReadoutName,
    OutputLevel=INFO
)
ecalBarrelPositionedCellsName = "ECalBarrelPositionedCells"
createEcalBarrelPositionedCells = CreateCaloCellPositionsFCCee(
    "CreateECalBarrelPositionedCells",
    OutputLevel=INFO
)
createEcalBarrelPositionedCells.positionsTool = cellPositionEcalBarrelTool
createEcalBarrelPositionedCells.hits.Path = ecalBarrelCellsName
createEcalBarrelPositionedCells.positionedHits.Path = ecalBarrelPositionedCellsName

cellPositionEcalBarrelTool2 = CellPositionsECalBarrelModuleThetaSegTool(
    "CellPositionsECalBarrel2",
    readoutName=ecalBarrelReadoutName2,
    OutputLevel=INFO
)
createEcalBarrelPositionedCells2 = CreateCaloCellPositionsFCCee(
    "CreateECalBarrelPositionedCells2",
    OutputLevel=INFO
)
createEcalBarrelPositionedCells2.positionsTool = cellPositionEcalBarrelTool2
createEcalBarrelPositionedCells2.hits.Path = ecalBarrelCellsName2
createEcalBarrelPositionedCells2.positionedHits.Path = "ECalBarrelPositionedCells2"

# Create cells in ECal endcap
createEcalEndcapCells = CreateCaloCells("CreateEcalEndcapCaloCells",
                                        doCellCalibration=True,
                                        calibTool=calibEcalEndcap,
                                        addCellNoise=False,
                                        filterCellNoise=False,
                                        OutputLevel=INFO)
createEcalEndcapCells.hits.Path = "ECalEndcapHits"
createEcalEndcapCells.cells.Path = "ECalEndcapCells"

if addNoise:
    ecalBarrelNoisePath = os.environ['FCCBASEDIR']+"/LAr_scripts/data/elecNoise_ecalBarrelFCCee_theta.root"
    ecalBarrelNoiseRMSHistName = "h_elecNoise_fcc_"
    from Configurables import NoiseCaloCellsVsThetaFromFileTool
    noiseBarrel = NoiseCaloCellsVsThetaFromFileTool("NoiseBarrel",
                                                    cellPositionsTool=cellPositionEcalBarrelTool,
                                                    readoutName=ecalBarrelReadoutName,
                                                    noiseFileName=ecalBarrelNoisePath,
                                                    elecNoiseRMSHistoName=ecalBarrelNoiseRMSHistName,
                                                    setNoiseOffset=False,
                                                    activeFieldName="layer",
                                                    addPileup=False,
                                                    filterNoiseThreshold=0,
                                                    numRadialLayers=11,
                                                    scaleFactor=1 / 1000.,  # MeV to GeV
                                                    OutputLevel=INFO)

    # barrel geometry tool is migrated to match ALLEGRO v3 segmentation
    from Configurables import TubeLayerModuleThetaMergedCaloTool
    barrelGeometry = TubeLayerModuleThetaMergedCaloTool("EcalBarrelGeo",
                                             readoutName=ecalBarrelReadoutName,
                                             activeVolumeName="LAr_sensitive",
                                             activeFieldName="layer",
                                             activeVolumesNumber=11,
                                             fieldNames=["system"],
                                             fieldValues=[4])
    
    # cells with noise not filtered
    createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCellsNoise",
                                                 doCellCalibration=True,
                                                 calibTool=calibEcalBarrel,
                                                 addCellNoise=True,
                                                 filterCellNoise=False,
                                                 noiseTool=noiseBarrel,
                                                 addPosition=True,
                                                 geometryTool=barrelGeometry,
                                                 OutputLevel=INFO,
                                                 hits=ecalBarrelHitsName,
                                                 cells=ecalBarrelCellsName)

    # cells with noise filtered
    # createEcalBarrelCellsNoise = CreateCaloCells("CreateECalBarrelCellsNoise_filtered",
    #                                              doCellCalibration=False,
    #                                              addCellNoise=True,
    #                                              filterCellNoise=True,
    #                                              OutputLevel=INFO,
    #                                              hits="ECalBarrelCellsStep2",
    #                                              noiseTool=noiseBarrel,
    #                                              geometryTool=barrelGeometry,
    #                                              cells=EcalBarrelCellsName)

if runHCal:
    # Create cells in HCal barrel
    # 1 - merge hits into cells with the default readout
    hcalBarrelCellsName = "HCalBarrelCells"
    createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                            doCellCalibration=True,
                                            calibTool=calibHcells,
                                            addCellNoise=False,
                                            filterCellNoise=False,
                                            addPosition=True,
                                            hits=hcalBarrelHitsName,
                                            cells=hcalBarrelCellsName,
                                            OutputLevel=INFO)

    # 2 - attach positions to the cells (cell positions needed for RedoSegmentation!)
    from Configurables import CellPositionsHCalBarrelPhiThetaSegTool
    cellPositionHcalBarrelTool = CellPositionsHCalBarrelPhiThetaSegTool(
        "CellPositionsHCalBarrel",
        readoutName=hcalBarrelReadoutName,
        OutputLevel=INFO
    )
    hcalBarrelPositionedCellsName = "HCalBarrelPositionedCells"
    createHcalBarrelPositionedCells = CreateCaloCellPositionsFCCee(
        "CreateHcalBarrelPositionedCells",
        OutputLevel=INFO
    )
    createHcalBarrelPositionedCells.positionsTool = cellPositionHcalBarrelTool
    createHcalBarrelPositionedCells.hits.Path = hcalBarrelCellsName
    createHcalBarrelPositionedCells.positionedHits.Path = hcalBarrelPositionedCellsName

    # 3 - compute new cellID of cells based on new readout - removing row information
    # We use a RedoSegmentation. Using a RewriteBitField with removeIds=["row"],
    # wont work because there are tiles with same layer/theta/phi but different row
    # as a consequence there will be multiple cells with same cellID in the output collection
    # and this will screw up the SW clustering
    hcalBarrelCellsName2 = "HCalBarrelCells2"

    # first we create new hits with the readout without the row information
    # and then merge them into new cells
    rewriteHCalBarrel = RedoSegmentation("ReSegmentationHcal",
                                         # old bitfield (readout)
                                         oldReadoutName=hcalBarrelReadoutName,
                                         # specify which fields are going to be altered (deleted/rewritten)
                                         oldSegmentationIds=["row", "theta", "phi"],
                                         # new bitfield (readout), with new segmentation (theta-phi grid)
                                         newReadoutName=hcalBarrelReadoutName2,
                                         OutputLevel=INFO,
                                         debugPrint=200,
                                         inhits=hcalBarrelPositionedCellsName,
                                         outhits="HCalBarrelCellsWithoutRow")

    createHcalBarrelCells2 = CreateCaloCells("CreateHCalBarrelCells2",
                                             doCellCalibration=False,
                                             addCellNoise=False,
                                             filterCellNoise=False,
                                             OutputLevel=INFO,
                                             hits=rewriteHCalBarrel.outhits.Path,
                                             cells=hcalBarrelCellsName2)

    # 4 - attach positions to the new cells
    from Configurables import CellPositionsHCalBarrelPhiThetaSegTool
    hcalBarrelPositionedCellsName2 = "HCalBarrelPositionedCells2"
    cellPositionHcalBarrelTool2 = CellPositionsHCalBarrelPhiThetaSegTool(
        "CellPositionsHCalBarrel2",
        readoutName=hcalBarrelReadoutName2,
        OutputLevel=INFO
    )
    createHcalBarrelPositionedCells2 = CreateCaloCellPositionsFCCee(
        "CreateHCalBarrelPositionedCells2",
        OutputLevel=INFO
    )
    createHcalBarrelPositionedCells2.positionsTool = cellPositionHcalBarrelTool2
    createHcalBarrelPositionedCells2.hits.Path = hcalBarrelCellsName2
    createHcalBarrelPositionedCells2.positionedHits.Path = hcalBarrelPositionedCellsName2

    # Create cells in HCal endcap
    # createHcalEndcapCells = CreateCaloCells("CreateHcalEndcapCaloCells",
    #                                    doCellCalibration=True,
    #                                    calibTool=calibHcalEndcap,
    #                                    addCellNoise=False,
    #                                    filterCellNoise=False,
    #                                    OutputLevel=INFO)
    # createHcalEndcapCells.hits.Path="HCalEndcapHits"
    # createHcalEndcapCells.cells.Path="HCalEndcapCells"

    # TODO: noise...
    
else:
    hcalBarrelCellsName = "emptyCaloCells"
    hcalBarrelPositionedCellsName = "emptyCaloCells"
    hcalBarrelCellsName2 = "emptyCaloCells"
    hcalBarrelPositionedCellsName2 = "emptyCaloCells"
    cellPositionHcalBarrelTool = None
    cellPositionHcalBarrelTool2 = None

# Empty cells for parts of calorimeter not implemented yet
createemptycells = CreateEmptyCaloCellsCollection("CreateEmptyCaloCells")
createemptycells.cells.Path = "emptyCaloCells"

# Produce sliding window clusters
if doSWClustering:
    towers = CaloTowerToolFCCee("towers",
                                deltaThetaTower=4 * 0.009817477 / 4, deltaPhiTower=2 * 2 * pi / 1536.,
                                ecalBarrelReadoutName=ecalBarrelReadoutName,
                                ecalEndcapReadoutName=ecalEndcapReadoutName,
                                ecalFwdReadoutName="",
                                hcalBarrelReadoutName=hcalBarrelReadoutName2,
                                hcalExtBarrelReadoutName="",
                                hcalEndcapReadoutName="",
                                hcalFwdReadoutName="",
                                OutputLevel=INFO)
    towers.ecalBarrelCells.Path = ecalBarrelPositionedCellsName
    towers.ecalEndcapCells.Path = "ECalEndcapCells"
    towers.ecalFwdCells.Path = "emptyCaloCells"
    towers.hcalBarrelCells.Path = hcalBarrelPositionedCellsName2
    towers.hcalExtBarrelCells.Path = "emptyCaloCells"
    towers.hcalEndcapCells.Path = "emptyCaloCells"
    towers.hcalFwdCells.Path = "emptyCaloCells"

    # Cluster variables
    windT = 9
    windP = 17
    posT = 5
    posP = 11
    dupT = 7
    dupP = 13
    finT = 9
    finP = 17
    # Minimal energy to create a cluster in GeV (FCC-ee detectors have to reconstruct low energy particles)
    threshold = 0.040

    createClusters = CreateCaloClustersSlidingWindowFCCee("CreateClusters",
                                                          towerTool=towers,
                                                          nThetaWindow=windT, nPhiWindow=windP,
                                                          nThetaPosition=posT, nPhiPosition=posP,
                                                          nThetaDuplicates=dupT, nPhiDuplicates=dupP,
                                                          nThetaFinal=finT, nPhiFinal=finP,
                                                          energyThreshold=threshold,
                                                          energySharingCorrection=False,
                                                          attachCells=True,
                                                          OutputLevel=INFO
                                                          )
    createClusters.clusters.Path = "CaloClusters"
    createClusters.clusterCells.Path = "CaloClusterCells"

    if applyUpDownstreamCorrections:
        correctCaloClusters = CorrectCaloClusters("correctCaloClusters",
                                                  inClusters=createClusters.clusters.Path,
                                                  outClusters="Corrected" + createClusters.clusters.Path,
                                                  numLayers=[11],
                                                  firstLayerIDs=[0],
                                                  lastLayerIDs=[10],
                                                  systemIDs=[4],
                                                  readoutNames=[ecalBarrelReadoutName],
                                                  # do not split the following line or it will break scripts that update the values of the corrections
                                                  upstreamParameters = [[0.025582045561310333, -0.9524128168665387, -53.10089405478649, 1.283851527438571, -295.30650178662637, -284.8945817377308]],
                                                  upstreamFormulas=[
                                                      ['[0]+[1]/(x-[2])', '[0]+[1]/(x-[2])']],
                                                  # do not split the following line or it will break scripts that update the values of the corrections
                                                  downstreamParameters = [[0.0018280333929494054, 0.004932212590963076, 0.8409676097173655, -1.2676690014715288, 0.005347798049886769, 4.161741293789687]],
                                                  downstreamFormulas=[
                                                      ['[0]+[1]*x', '[0]+[1]/sqrt(x)', '[0]+[1]/x']],
                                                  OutputLevel=INFO
                                                  )

    if addShapeParameters:
        augmentCaloClusters = AugmentClustersFCCee("augmentCaloClusters",
                                                   inClusters=createClusters.clusters.Path,
                                                   outClusters="Augmented" + createClusters.clusters.Path,
                                                   systemIDs=[4],
                                                   systemNames=["EMB"],
                                                   numLayers=[11],
                                                   readoutNames=[ecalBarrelReadoutName],
                                                   layerFieldNames=["layer"],
                                                   # use default values
                                                   #thetaRecalcWeights=[
                                                   #    [-1, 3.0, 3.0, 3.0, 4.25, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]  # -1 : use linear weights
                                                   #],
                                                   OutputLevel=INFO
                                                   )

    if applyMVAClusterEnergyCalibration:
        inClusters = ""
        if addShapeParameters:
            inClusters = "Augmented" + createClusters.clusters.Path
        else:
            inClusters = createClusters.clusters.Path

        calibrateCaloClusters = CalibrateCaloClusters("calibrateCaloClusters",
                                                      inClusters=inClusters,
                                                      outClusters="Calibrated" + createClusters.clusters.Path,
                                                      systemIDs=[4],
                                                      systemNames=["EMB"],
                                                      numLayers=[11],
                                                      firstLayerIDs=[0],
                                                      readoutNames=[
                                                          ecalBarrelReadoutName],
                                                      layerFieldNames=["layer"],
                                                      calibrationFile=os.environ['FCCBASEDIR'] + "/LAr_scripts/data/lgbm_calibration-CaloClusters-v03.onnx",
                                                      OutputLevel=INFO
                                                      )


# Produce topological clusters
if doTopoClustering:
    createTopoInput = CaloTopoClusterInputTool("CreateTopoInput",
                                               ecalBarrelReadoutName=ecalBarrelReadoutName,
                                               ecalEndcapReadoutName="",
                                               ecalFwdReadoutName="",
                                               hcalBarrelReadoutName=hcalBarrelReadoutName2,
                                               hcalExtBarrelReadoutName="",
                                               hcalEndcapReadoutName="",
                                               hcalFwdReadoutName="",
                                               OutputLevel=INFO)

    createTopoInput.ecalBarrelCells.Path = ecalBarrelPositionedCellsName
    createTopoInput.ecalEndcapCells.Path = "emptyCaloCells"
    createTopoInput.ecalFwdCells.Path = "emptyCaloCells"
    createTopoInput.hcalBarrelCells.Path = hcalBarrelPositionedCellsName2
    createTopoInput.hcalExtBarrelCells.Path = "emptyCaloCells"
    createTopoInput.hcalEndcapCells.Path = "emptyCaloCells"
    createTopoInput.hcalFwdCells.Path = "emptyCaloCells"
    cellPositionHcalBarrelNoSegTool = None
    cellPositionHcalExtBarrelTool = None

    neighboursMap = "/LAr_scripts/data/neighbours_map_v03_ecalB_thetamodulemerged.root"
    noiseMap = "/LAr_scripts/data/cellNoise_map_electronicsNoiseLevel_v03_ecalB_thetamodulemerged.root"
    if runHCal:
        neighboursMap = "/LAr_scripts/data/neighbours_map_v03_ecalB_thetamodulemerged_hcalB_thetaphi.root"
        noiseMap = "/LAr_scripts/data/cellNoise_map_electronicsNoiseLevel_v03_ecalB_thetamodulemerged_hcalB_thetaphi.root"

    readNeighboursMap = TopoCaloNeighbours("ReadNeighboursMap",
                                           fileName=os.environ['FCCBASEDIR'] + neighboursMap,
                                           OutputLevel=INFO)

    # Noise levels per cell
    readNoisyCellsMap = TopoCaloNoisyCells("ReadNoisyCellsMap",
                                           fileName=os.environ['FCCBASEDIR'] + noiseMap,
                                           OutputLevel=INFO)

    createTopoClusters = CaloTopoClusterFCCee("CreateTopoClusters",
                                              TopoClusterInput=createTopoInput,
                                              # expects neighbours map from cellid->vec < neighbourIds >
                                              neigboursTool=readNeighboursMap,
                                              # tool to get noise level per cellid
                                              noiseTool=readNoisyCellsMap,
                                              # cell positions tools for all sub - systems
                                              positionsECalBarrelTool=cellPositionEcalBarrelTool,
                                              positionsHCalBarrelTool=cellPositionHcalBarrelTool2,
                                              # positionsHCalBarrelNoSegTool=cellPositionHcalBarrelNoSegTool,
                                              # positionsHCalExtBarrelTool=cellPositionHcalExtBarrelTool,
                                              # positionsHCalExtBarrelTool = HCalExtBcells,
                                              # positionsEMECTool = EMECcells,
                                              # positionsHECTool = HECcells,
                                              # positionsEMFwdTool = ECalFwdcells,
                                              # positionsHFwdTool = HCalFwdcells,
                                              noSegmentationHCal=False,
                                              seedSigma=4,
                                              neighbourSigma=2,
                                              lastNeighbourSigma=0,
                                              OutputLevel=INFO)
    createTopoClusters.clusters.Path = "CaloTopoClusters"
    createTopoClusters.clusterCells.Path = "CaloTopoClusterCells"

    # Correction below is for EM-only clusters
    # Need something different for EM+HCAL
    if applyUpDownstreamCorrections:
        correctCaloTopoClusters = CorrectCaloClusters(
            "correctCaloTopoClusters",
            inClusters=createTopoClusters.clusters.Path,
            outClusters="Corrected" + createTopoClusters.clusters.Path,
            systemIDs=[4],
            numLayers=[11],
            firstLayerIDs=[0],
            lastLayerIDs=[10],
            readoutNames=[ecalBarrelReadoutName],
            # do not split the following line or it will break scripts that update the values of the corrections
            upstreamParameters = [[0.025582045561310333, -0.9524128168665387, -53.10089405478649, 1.283851527438571, -295.30650178662637, -284.8945817377308]],
            upstreamFormulas=[['[0]+[1]/(x-[2])', '[0]+[1]/(x-[2])']],
            # do not split the following line or it will break scripts that update the values of the corrections
            downstreamParameters = [[0.0018280333929494054, 0.004932212590963076, 0.8409676097173655, -1.2676690014715288, 0.005347798049886769, 4.161741293789687]],
            downstreamFormulas=[['[0]+[1]*x', '[0]+[1]/sqrt(x)', '[0]+[1]/x']],
            OutputLevel=INFO
        )

    if addShapeParameters:
        augmentCaloTopoClusters = AugmentClustersFCCee("augmentCaloTopoClusters",
                                                       inClusters=createTopoClusters.clusters.Path,
                                                       outClusters="Augmented" + createTopoClusters.clusters.Path,
                                                       systemIDs=[4],
                                                       systemNames=["EMB"],
                                                       numLayers=[11],
                                                       readoutNames=[ecalBarrelReadoutName],
                                                       layerFieldNames=["layer"],
                                                       # use default weights
                                                       # thetaRecalcWeights=[
                                                       #     [-1, 3.0, 3.0, 3.0, 4.25, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]  # -1 : use linear weights
                                                       # ],
                                                       OutputLevel=INFO)

    if applyMVAClusterEnergyCalibration:
        inClusters = ""
        if addShapeParameters:
            inClusters = "Augmented" + createTopoClusters.clusters.Path
        else:
            inClusters = createTopoClusters.clusters.Path,
        calibrateCaloTopoClusters = CalibrateCaloClusters("calibrateCaloTopoClusters",
                                                          inClusters=inClusters,
                                                          outClusters="Calibrated" + createTopoClusters.clusters.Path,
                                                          systemIDs=[4],
                                                          systemNames=["EMB"],
                                                          numLayers=[11],
                                                          firstLayerIDs=[0],
                                                          readoutNames=[
                                                              ecalBarrelReadoutName],
                                                          layerFieldNames=["layer"],
                                                          calibrationFile=os.environ['FCCBASEDIR'] + "/LAr_scripts/data/lgbm_calibration-CaloTopoClusters-v03.onnx",
                                                          OutputLevel=INFO
                                                          )

# Output
out = PodioOutput("out",
                  OutputLevel=INFO)

if runHCal:
    out.outputCommands = ["keep *", "drop emptyCaloCells"]
else:
    out.outputCommands = ["keep *", "drop HCal*", "drop emptyCaloCells"]

if not saveCells:
    out.outputCommands.append("drop ECal*Cells*")
if not saveClusterCells:
    out.outputCommands.append("drop *ClusterCells*")
if not saveHits:
    out.outputCommands.append("drop ECal*Hits*")

# out.filename = "root/output_fullCalo_SimAndDigi_withTopoCluster_MagneticField_"+str(magneticField)+"_pMin_"+str(momentum*1000)+"_MeV"+"_ThetaMinMax_"+str(thetaMin)+"_"+str(thetaMax)+"_pdgId_"+str(pdgCode)+"_pythia"+str(use_pythia)+"_Noise"+str(addNoise)+".root"
out.filename = "./root/output_evts_" + str(Nevts) + "_pdg_" + str(pdgCode) + "_" + str(momentum) + "_GeV" + "_ThetaMinMax_" + str(thetaMin) + "_" + str(
    thetaMax) + "_PhiMinMax_" + str(phiMin) + "_" + str(phiMax) + "_MagneticField_" + str(magneticField) + "_Noise" + str(addNoise) + ".root"

# CPU information
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
genAlg.AuditExecute = True
hepmc_converter.AuditExecute = True
geantsim.AuditExecute = True
createEcalBarrelCells.AuditExecute = True
createEcalBarrelPositionedCells.AuditExecute = True
if runHCal:
    createHcalBarrelCells.AuditExecute = True
if doTopoClustering:
    createTopoClusters.AuditExecute = True
out.AuditExecute = True

event_counter = EventCounter('event_counter')
event_counter.Frequency = 10

ExtSvc = [geoservice, podioevent, geantservice, audsvc]
if dumpGDML:
    ExtSvc += [gdmldumpservice]

TopAlg = [
    event_counter,
    genAlg,
    hepmc_converter,
    geantsim,
    createEcalBarrelCells,
    createEcalBarrelPositionedCells,
    resegmentEcalBarrel,
    createEcalBarrelCells2,
    createEcalBarrelPositionedCells2,
    createEcalEndcapCells,
]

if runHCal:
    TopAlg += [
        createHcalBarrelCells,
        createHcalBarrelPositionedCells,
        rewriteHCalBarrel,
        createHcalBarrelCells2,
        createHcalBarrelPositionedCells2,
        # createHcalEndcapCells
    ]

if doSWClustering or doTopoClustering:
    TopAlg += [createemptycells]

    if doSWClustering:
        TopAlg += [createClusters]

        if applyUpDownstreamCorrections:
            TopAlg += [correctCaloClusters]

        if addShapeParameters:
            TopAlg += [augmentCaloClusters]

        if applyMVAClusterEnergyCalibration:
            TopAlg += [calibrateCaloClusters]

    if doTopoClustering:
        TopAlg += [createTopoClusters]

        if applyUpDownstreamCorrections:
            TopAlg += [correctCaloTopoClusters]

        if addShapeParameters:
            TopAlg += [augmentCaloTopoClusters]

        if applyMVAClusterEnergyCalibration:
            TopAlg += [calibrateCaloTopoClusters]

TopAlg += [
    out
]

ApplicationMgr(
    TopAlg=TopAlg,
    EvtSel='NONE',
    EvtMax=Nevts,
    ExtSvc=ExtSvc,
    StopOnSignal=True,
)
