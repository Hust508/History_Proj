if {[catch {
    import_device ph1_35p.db -package PH1P35MDG324 -speed 3
    open_project lab_ex2_edge_dsi_SC500_7inch.al
} taskError]} {
    puts stderr $taskError
    exit 1
}
puts "EDGE_DSI_PROJECT_OPEN_OK"
exit
