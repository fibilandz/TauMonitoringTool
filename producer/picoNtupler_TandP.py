import os
import sys

import ROOT

# Enable multi-threading                                                                                                                                                                                    
ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)


import argparse

parser = argparse.ArgumentParser(description='Skim full tuple.')
parser.add_argument('--input', required=False, type=str, nargs='+', help="input files")
parser.add_argument('--channel', required=True, type=str, help="ditau,mutau or etau")
parser.add_argument('--run', required=True, type=str, help="tau selection")
parser.add_argument('--plot', required=True, type=str, help="plot name")
parser.add_argument('--iseta',action='store_true', help="plot name")
parser.add_argument('--var', required=True, type=str, help="tau_pt, tau_eta, jet_pt, jet_eta")

args = parser.parse_args()



core_dir = str(os.getcwd()).split('producer')

Trigger_header_path = os.path.join(core_dir[0] +'/interface' + os.sep,"picoNtupler.h")

ROOT.gInterpreter.Declare('#include "{}"'.format(Trigger_header_path))

sys.path.insert(1, core_dir[0]+'/python')
from RooPlottingTool import *


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
    "/eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/anayak/2022NanoAOD/Muon_Fill8102/Run356956/",
]
inputFiles = []

for folder in folders:
    files = os.listdir(folder)
    inputFiles += [folder + f for f in files]

df = ROOT.RDataFrame("Events", tuple(inputFiles))


# Tag And Probe selection {Obtaining high pure Z -> mu tau Events}

## select muon (Tag) candidate 

df_tag = df.Filter("nMuon == 1 && nTau >=1").Define("Muon_Index","MuonIndex(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,nMuon,Muon_pt,Muon_eta,Muon_phi,Muon_mass,Muon_pfRelIso04_all)").Define("muon_p4","Obj_p4(Muon_Index,Muon_pt,Muon_eta,Muon_phi,Muon_mass)")

## select tau (probe) candidate

df_probe = df_tag.Filter("Muon_Index >= 0").Define("Tau_Index","TauIndex(nTau, Tau_pt, Tau_eta, Tau_phi, Tau_mass, Tau_dz, muon_p4)")

df_probe_id = df_probe.Filter("Tau_Index >= 0 && Tau_idDeepTau2017v2p1VSjet[Tau_Index] >=16 && Tau_idDeepTau2017v2p1VSmu[Tau_Index] >=8 && Tau_idDeepTau2017v2p1VSe[Tau_Index] >=2").Define("tau_p4","Obj_p4(Tau_Index,Tau_pt,Tau_eta,Tau_phi,Tau_mass)")


# Calculate Efficiency

# denominator histogram
if args.channel != 'ditaujet_jetleg':
    ## select mu-tau pair with os and ss events
    df_TandP_os = df_probe_id.Define('weight',"(Tau_charge[Tau_Index] != Muon_charge[Tau_Index]) ? 1. : -1.").Define("mT","CalcMT(muon_p4,MET_pt,MET_phi)").Define("m_vis","ZMass(tau_p4,muon_p4)")
    ## select pure Z -> mu tau events
    df_TandP = df_TandP_os.Filter("mT < 30 && m_vis > 40 && m_vis < 80").Define("tau_pt","Tau_pt[Tau_Index]").Define("tau_eta","Tau_eta[Tau_Index]")
    df_TandP_den_filt = df_TandP
    h_den_os = df_TandP_den_filt.Histo1D(CreateHistModel("denominator",args.iseta),args.var)
else:
    assert "jet" in args.var 
    df_TandP_den = df_probe_id.Define("pass_ditau",
        "PassDiTauFilter(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,Tau_pt[Tau_Index],Tau_eta[Tau_Index],Tau_phi[Tau_Index])")

    # df_TandP_den = df_TandP_den.Define("Jet_Index","JetIndex(nJet, Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_puId, Jet_jetId, muon_p4, tau_p4)" # PU ID not present in this nanoAOD, skipped
    df_TandP_den = df_TandP_den.Define("Jet_Index","JetIndex(nJet, Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_jetId, muon_p4, tau_p4)"
        ).Filter("Jet_Index >= 0").Define("jet_pt","Jet_pt[Jet_Index]").Define("jet_eta","Jet_eta[Jet_Index]")
    df_TandP_den_filt = df_TandP_den.Filter("pass_ditau > 0.5 && HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1 == 1")
    h_den_os = df_TandP_den_filt.Histo1D(CreateHistModel("denominator",args.iseta), args.var)

# numerator histogram
if args.channel == 'ditau':
    df_TandP_num = df_TandP_den_filt.Define("pass_ditau","PassDiTauFilter(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,Tau_pt[Tau_Index],Tau_eta[Tau_Index],Tau_phi[Tau_Index])")
    h_num_os = df_TandP_num.Filter("pass_ditau > 0.5 && HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1 == 1").Histo1D(CreateHistModel("numerator",args.iseta),args.var,'weight')
    # h = df_TandP_num.Histo1D('weight')
elif args.channel == 'mutau':
    df_TandP_num = df_TandP_den_filt.Define("pass_mutau","PassMuTauFilter(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,Tau_pt[Tau_Index],Tau_eta[Tau_Index],Tau_phi[Tau_Index])")
    h_num_os = df_TandP_num.Filter("pass_mutau > 0.5 && HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1==1").Histo1D(CreateHistModel("numerator",args.iseta),args.var,'weight')
elif args.channel == 'ditaujet_tauleg':
    df_TandP_num = df_TandP_den_filt.Define("pass_ditau","PassDiTauFilter(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,Tau_pt[Tau_Index],Tau_eta[Tau_Index],Tau_phi[Tau_Index])")
    h_num_os = df_TandP_num.Filter("pass_ditau > 0.5 && HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1 == 1").Histo1D(CreateHistModel("numerator",args.iseta),args.var,'weight')
elif args.channel == 'ditaujet_jetleg':
    df_TandP_num = df_TandP_den_filt.Define("pass_ditau_jet","PassDiTauJetFilter(nTrigObj,TrigObj_id,TrigObj_filterBits,TrigObj_pt,TrigObj_eta,TrigObj_phi,Jet_pt[Jet_Index],Jet_eta[Jet_Index],Jet_phi[Jet_Index])")
    h_num_os = df_TandP_num.Filter("pass_ditau_jet > 0.5 && HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet60_CrossL1 == 1").Histo1D(CreateHistModel("numerator",args.iseta),args.var)
else:
    raise ValueError()

## Produce plot                 
print("Create TurnON")                                                                                                                                                                         
ROOT.gStyle.SetOptStat(0); ROOT.gStyle.SetTextFont(42)
c = ROOT.TCanvas("c", "", 800, 700)

gr = ROOT.TEfficiency(h_num_os.GetPtr(),h_den_os.GetPtr())
gr.SetTitle("")
gr.Draw()

label = ROOT.TLatex(); label.SetNDC(True)
if(args.var == "tau_pt" or args.var=="tau_l1pt"):
    label.DrawLatex(0.8, 0.03, "#tau_pT")
elif(args.var == "jet_pt"):
    label.DrawLatex(0.8, 0.03, "jet_pT")
elif(args.var == "jet_eta"):
    label.DrawLatex(0.8, 0.03, "#eta_jet")
else:
    label.DrawLatex(0.8, 0.03, "#eta_#tau")
label.SetTextSize(0.040); label.DrawLatex(0.100, 0.920, "#bf{CMS Run3 Data}")
label.SetTextSize(0.030); label.DrawLatex(0.630, 0.920, "#sqrt{s} = 13.6 TeV, "+args.run)

c.SaveAs("%s_%s.pdf" % (args.plot, args.channel))

