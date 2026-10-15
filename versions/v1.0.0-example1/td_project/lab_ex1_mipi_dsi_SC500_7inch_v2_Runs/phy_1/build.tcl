if {[catch {source {C:/APP2/ALTD/doc/scripts/DefaultFlow.tcl}} taskError]} {
    puts stderr $taskError
    exit 1
}
set_param bitgen compress on
bitgen -bit lab_ex1_mipi_dsi_SC500_7inch_v2.bit
exit
