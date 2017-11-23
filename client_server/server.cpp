//
//  main.cpp
//  client_server
//
//  Created by Aous Naman on 6/03/2015.
//  Copyright (c) 2015 Aous Naman. All rights reserved.
//

#include "server.h"

/////////////////////////////////////////////////////////////////////////////
void udp_server::handle_receive(const error_code& ec, std::size_t length) {
  //check to which client and send the data over for processing
  // if the client is not yet known, create a new client
  high_resolution_timer::time_point cur_time;
  cur_time = high_resolution_timer::clock_type::now();
  
  udp_clients_map::iterator it = clients_map.find(remote_ep);
  if (it == clients_map.end()) { //client not found
    if (sdn) sdn->register_client(remote_ep.address());
    udp_svr_client* client;
    client = new udp_svr_client(srvc, remote_ep, get_duration(2e9),
                                cur_time, rcv_buf, length, this,
                                on_off_transitions);
    clients_map.insert(udp_clients_pair(remote_ep, client));
  }
  else
    it->second->data_received(cur_time, rcv_buf, length);
  
  socket.async_receive_from(boost::asio::buffer(rcv_buf, sizeof(rcv_buf)),
                            remote_ep,
                            boost::bind(&udp_server::handle_receive, this,
                                             _1, _2));
}


/////////////////////////////////////////////////////////////////////////////
int main(int argc, char* argv[]) {

  if (argc != 6) {
    std::cerr << "Usage: server <local address> <local port> "
    "<sdn address> <sdn port> <0 no on_off_trans, 1 on_off_trans>"<< std::endl;
    return 1;
  }
  
  io_service service;
  
  address local_address = address::from_string(argv[1]);
  udp::endpoint local_endpoint(local_address, atoi(argv[2]));
  tcp::resolver resolver(service);
  tcp::resolver::query query(tcp::v4(), argv[3], argv[4]);
  tcp::endpoint sdn_endpoint = *resolver.resolve(query);
  
  try {
    sdn_manager sdn(service, sdn_endpoint, local_address, 3e9);
    udp_server server(service, &sdn, argv[5][0] != '0');
    server.start(local_endpoint);
    service.run();
  } catch (std::exception& e) {
    std::cerr << e.what() << std::endl;
  }
}

