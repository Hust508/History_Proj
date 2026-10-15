import_device ph1_35p.db -package PH1P35MDG324 -speed 3
open_project lab_ex1_mipi_dsi_SC500_7inch_v2.prj -noanalyze
import_db lab_ex1_mipi_dsi_SC500_7inch_v2_pr.db
commit_param -step bitgen
set_param bitgen compress on
bitgen -bit lab_ex1_mipi_dsi_SC500_7inch_v2.bit
exit
