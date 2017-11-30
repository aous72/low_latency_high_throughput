//
//  client.cpp
//  client_server
//
//  Created by Aous Naman on 8/03/2015.
//  Copyright (c) 2015 Aous Naman. All rights reserved.
//

#include <cstdlib>
#include <iostream>
#include <cmath>

#include <boost/bind.hpp>

#include <boost/asio/high_resolution_timer.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/ip/udp.hpp>
#include <boost/asio/ip/tcp.hpp>

using boost::asio::io_service;
using boost::asio::high_resolution_timer;
using boost::asio::ip::udp;
using boost::asio::ip::address;
using boost::system::error_code;

/////////////////////////////////////////////////////////////////////////////
high_resolution_timer::duration get_duration(double nanosecs) {
  double t = round(nanosecs);
  return high_resolution_timer::duration(static_cast<int_least64_t>(t));
}

/////////////////////////////////////////////////////////////////////////////
struct send_data {
  send_data() : last_message_number(0), time_tick(false) {}
  operator const char *() const { return (char *)this; }
  int last_message_number;
  bool time_tick;
};

/////////////////////////////////////////////////////////////////////////////
class udp_client {
public:
  udp_client()
  : srvc(NULL), socket(NULL), timer(NULL), rslvr(NULL), initial_port(0),
  ms_timeout(0), timeout_counter(0), last_message(0), id(-1), data_file(NULL)
  {
    memset(recv_buf, 0, sizeof(recv_buf));
  }
  
  ~udp_client() {
    if (socket) {
      socket->cancel();
      socket->close();
      delete socket;
    }
    if (timer) delete timer;
    if (data_file) fclose(data_file);
    std::cout << "Client Terminating" << std::endl;
  }
  
  void start(int id, io_service &service, udp::resolver& resolver,
             const char *target_name, const char *target_port,
             int millisecond_timeout, bool store_bw) {
    assert(this->id == -1 && id >= 0);
    this->id = id;
    if (store_bw)
      data_file = fopen("client_data.txt", "wt");
    assert(srvc == NULL && rslvr == NULL && timer == NULL && socket == NULL);
    srvc = &service;
    rslvr = &resolver;
    timer = new high_resolution_timer(service);
    socket = new udp::socket(service);
    socket->open(udp::v4());

    ms_timeout = millisecond_timeout;
    udp::resolver::query query(udp::v4(), target_name, target_port);
    rslvr->async_resolve(query,
                         boost::bind(&udp_client::handle_name_resolution,
                                     this, _1, _2));
  }
  
protected: //static callback members
  void handle_receive(const error_code& ec, std::size_t length) {
    if (!ec) {
      int msg_number = *(int *)recv_buf;
      if (msg_number > send_buf.last_message_number)
        send_buf.last_message_number = msg_number;
    }
    timeout_counter = 0;
    socket->async_receive_from(boost::asio::buffer(recv_buf), dest_endpoint, 0,
                               boost::bind(&udp_client::handle_receive, this,
                                           _1, _2));
    send(false);
  }
  
  void handle_timeout(const error_code& error) {
    if (error == boost::asio::error::operation_aborted)
      return;

    int num_msgs = send_buf.last_message_number - last_message;
    last_message = send_buf.last_message_number;
    std::cout << "num messages = " << num_msgs << std::endl;
    if (data_file) {
      fprintf(data_file, "%d\n",num_msgs);
      fflush(data_file);
    }
    
    //prepare timeout
    timer->expires_from_now(get_duration(100e6));
    timer->async_wait(boost::bind(&udp_client::handle_timeout, this, _1));
    
    if (timeout_counter < 101)
      if (++timeout_counter >= 101) {
        dest_endpoint.port(initial_port);
        send_buf.last_message_number = 0;
        last_message = 0;
      }
    send(true);
  }
  
  void handle_name_resolution(const error_code& error,
                              udp::resolver::iterator iterator) {
    dest_endpoint = *iterator;
    initial_port = dest_endpoint.port();
    
    //prepare to receive data
    socket->async_receive_from(boost::asio::buffer(recv_buf),
                               dest_endpoint, 0,
                               boost::bind(&udp_client::handle_receive, this,
                                           _1, _2));
    //prepare timeout
    timer->expires_from_now(get_duration(250e6));
    timer->async_wait(boost::bind(&udp_client::handle_timeout, this, _1));

    //send request
    send(false);
  }
  
  void handle_send(const error_code& error, std::size_t bytes_transferred) {
    if (error)
      std::cout << error.message() << std::endl;
  }
  
protected: //protected members
  void send(bool time_tick) {
    send_buf.time_tick = time_tick;
    socket->async_send_to(boost::asio::buffer(send_buf, sizeof(send_buf)),
                          dest_endpoint,
                          boost::bind(&udp_client::handle_send, this,
                                     _1, _2));
  }
  
protected: //an id for the client, can be used for different things
  int id;
  FILE *data_file;
  
protected: //protected variables
  char recv_buf[6144]; //should be more then enough to hold one packet
  send_data send_buf;
  int last_message;
  
  udp::socket *socket;
  io_service *srvc;
  high_resolution_timer *timer;
  udp::resolver *rslvr; //to resolve the name
  udp::endpoint dest_endpoint;
  int ms_timeout, initial_port;
  int timeout_counter;
};

/////////////////////////////////////////////////////////////////////////////
int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: client <host> <port> <num clients> "
    "<client num which save bandwidth (Optional)>" << std::endl;
    return 1;
  }
  
  int num_clients = 1;
  if (argc >= 4)
    num_clients = atoi(argv[3]);
  bool store_bw = false;
  int client_num_storing_bw = 0;
  if (argc == 5) {
    store_bw = true;
    client_num_storing_bw = atoi(argv[4]);
  }
  
  io_service service;
  udp::resolver resolver(service);
  udp_client *clients = new udp_client[num_clients];
  for (int i = 0; i < num_clients; ++i)
    clients[i].start(i, service, resolver, argv[1], argv[2], 500,
                     store_bw && (i == client_num_storing_bw));
  service.run();
}





