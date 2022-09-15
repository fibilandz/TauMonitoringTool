import os
import sys

import ROOT

# Enable multi-threading                                                                                                                                                                                    
ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)

core_dir = str(os.getcwd()).split('producer')

Trigger_header_path = os.path.join(core_dir[0] + '/interface' + os.sep, "picoNtupler.h")

ROOT.gInterpreter.Declare('#include "{}"'.format(Trigger_header_path))

sys.path.insert(1, core_dir[0]+'/python')

from RooPlottingTool import *

# select the version
TauID_ver = sys.argv[1]
outFile   = sys.argv[2]

def create_rdataframe(folders, inputFiles=None):
    if not inputFiles:
        inputFiles = []
        for folder in folders:
            files = os.listdir(folder)
            inputFiles += [folder + f for f in files]

    return ROOT.RDataFrame("Events", tuple(inputFiles))

def obtain_picontuple(df):

    branches = []

    # Tag And Probe selection {Obtaining high pure Z -> mu tau Events}
    ## select muon (Tag) candidate

    df = df.Filter("nMuon == 1 && nTau >= 1")

    df = df.Define("Muon_Index", "MuonIndexFull(nTau, nTrigObj, TrigObj_id, TrigObj_filterBits, TrigObj_pt, TrigObj_eta, TrigObj_phi,\
        nMuon, Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_pfRelIso04_all)").Define("muon_p4",\
        "Obj_p4(Muon_Index, Muon_pt, Muon_eta, Muon_phi, Muon_mass)").Define("muon_iso","getFloatValue(Muon_pfRelIso04_all, Muon_Index)")
    branches += ["Muon_Index", "muon_iso"]

    ## select tau (probe) candidate
    df = df.Define("Tau_Index", "TauIndex(nTau, Tau_pt, Tau_eta, Tau_phi, Tau_mass, Tau_dz, muon_p4,Tau_rawIsodR03)")
    branches += ["HLT_IsoMu24_eta2p1", "Tau_Index"]

    if TauID_ver == '2p1':
        df = df.Define("Tau_goodid",
            "getIntValue(Tau_decayMode, Tau_Index) != 5 && "
            "getIntValue(Tau_decayMode, Tau_Index) != 6 && "
            "getIntValue(Tau_idDeepTau2017v2p1VSjet, Tau_Index) >= 16"
        ).Define("tau_p4","Obj_p4(Tau_Index, Tau_pt, Tau_eta, Tau_phi, Tau_mass)")
        branches += ["Tau_goodid", "Tau_decayMode", "Tau_idDeepTau2017v2p1VSjet"] 
    elif TauID_ver == '2p5':
        df = df.Define("Tau_goodid",
            "getIntValue(Tau_decayMode, Tau_Index) != 5 && "
            "getIntValue(Tau_decayMode, Tau_Index) != 6 && "
            "getIntValue(Tau_idDeepTau2018v2p5VSjet, Tau_Index) >= 5"
        ).Define("tau_p4","Obj_p4(Tau_Index, Tau_pt, Tau_eta, Tau_phi, Tau_mass)")
        branches += ["Tau_goodid", "Tau_decayMode", "Tau_idDeepTau2018v2p5VSjet"]

    # Calculate Efficiency
    df = df.Define('weight',
        "(getIntValue(Tau_charge, Tau_Index) != getIntValue(Muon_charge, Muon_Index)) ? 1. : -1."
    ).Define("mT", "CalcMT(muon_p4, MET_pt, MET_phi)").Define("m_vis", "ZMass(tau_p4, muon_p4)")
    branches += ["weight", "mT", "m_vis"]

    df = df.Define("passZmass", "mT < 30 && m_vis > 40 && m_vis < 80")
    branches += ["passZmass"]

    ## ditau and #ditaujet_tauleg
    df = df.Define("pass_ditau",
        "PassDiTauFilter(nTrigObj, TrigObj_id, TrigObj_filterBits, TrigObj_pt, TrigObj_eta, TrigObj_phi,\
        getFloatValue(Tau_pt, Tau_Index), getFloatValue(Tau_eta, Tau_Index), getFloatValue(Tau_phi, Tau_Index))")

    branches += ["pass_ditau"]

    df = df.Define("Jet_Index", "JetIndex(nJet, Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_jetId, muon_p4, tau_p4)")
    branches += ["Jet_Index", "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1", "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1"]

    # define numerators used more than once below
    PassMuTauFilter = "PassMuTauFilter(nTrigObj, TrigObj_id, TrigObj_filterBits, \
       TrigObj_pt, TrigObj_eta, TrigObj_phi, \
       getFloatValue(Tau_pt, Tau_Index), getFloatValue(Tau_eta, Tau_Index), getFloatValue(Tau_phi, Tau_Index))"

    ## mutau
    df = df.Define("pass_mutau", PassMuTauFilter)
    branches += ["pass_mutau", "HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1"]

    ## VBFasymtau_uppertauleg
    df = df.Define("pass_VBFasymtau_uppertauleg", PassMuTauFilter)
    branches += ["pass_VBFasymtau_uppertauleg", "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1"]

    ## 'VBFasymtau_lowertauleg
    branches += ["HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1"]

    ## VBF+ditau chargedIso Monitoring
    branches += ["HLT_IsoMu20_eta2p1_TightChargedIsoPFTauHPS27_eta2p1_TightID_CrossL1"]
    ## ditaujet_jetleg
    df = df.Define("pass_ditau_jet",
        "PassDiTauJetFilter(nTrigObj, TrigObj_id, TrigObj_filterBits, TrigObj_pt, TrigObj_eta, TrigObj_phi, \
        getFloatValue(Jet_pt, Jet_Index), getFloatValue(Jet_eta, Jet_Index), getFloatValue(Jet_phi, Jet_Index))")

    branches += ["pass_ditau_jet", "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet60_CrossL1"]

    return df, branches



if __name__ == '__main__':

    #inputFiles = (f'/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/SingleMuonV1/Files2/nano_aod_{i}.root' for i in range(0,79))

    folders = [
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356943/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356944/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356945/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356946/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356947/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356948/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356949/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356951/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356954/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356955/",
        "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356956/"
        # "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/savarghe/nanoaod/eraD/Fill8136/Muon/"
    ]

    df = create_rdataframe(folders)
    df, branches = obtain_picontuple(df)
    branches.sort()
    branches = [
        "nTau", "Tau_pt", "Tau_eta", "Tau_phi", "Tau_mass",
        "nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass",
        "nJet", "Jet_pt", "Jet_eta", "Jet_phi", "Jet_mass"] + branches
    branch_list = ROOT.vector('string')()
    for branch_name in branches:
        branch_list.push_back(branch_name)

    df.Snapshot("Events", './'+outFile+'.root', branch_list)
