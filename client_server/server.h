//
//  server.h
//  client_server
//
//  Created by Aous Naman on 11/03/2015.
//  Copyright (c) 2015 Aous Naman. All rights reserved.
//

#ifndef client_server_server_h
#define client_server_server_h

#include <cstdlib>
#include <iostream>

#include <map>
#include <chrono>

#include <boost/bind.hpp>

#include <boost/asio/high_resolution_timer.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/ip/udp.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/circular_buffer.hpp>

#include "sdn_manager.h"

using boost::asio::io_service;
using boost::asio::high_resolution_timer;
using boost::asio::ip::udp;
using boost::asio::ip::tcp;
using boost::asio::ip::address;
using boost::system::error_code;

class udp_svr_client;
class udp_server;

/////////////////////////////////////////////////////////////////////////////
struct rcv_data {
  rcv_data() : last_message_number(0), time_tick(false) {}
  operator char *() const { return (char *)this; }
  int last_message_number;
  bool time_tick;
};

/////////////////////////////////////////////////////////////////////////////
struct acknowledgment_info {
  acknowledgment_info()
  : num_bytes(0), time(high_resolution_timer::time_point::min()) {}
  acknowledgment_info(int num_bytes,
                      const high_resolution_timer::time_point& time)
  : num_bytes(num_bytes), time(time) {}
  int num_bytes;
  high_resolution_timer::time_point time;
};

/////////////////////////////////////////////////////////////////////////////
class udp_svr_client { //this class contains the client information
public:
  typedef boost::circular_buffer<acknowledgment_info> ack_buffer;
  
  udp_svr_client(io_service& service, udp::endpoint client_endpoint,
                 const high_resolution_timer::duration& timeout,
                 const high_resolution_timer::time_point &timestamp,
                 const rcv_data& rcv, std::size_t length, udp_server *server,
                 bool on_off_transitions)
  : socket(service), srvc(service), timer(service), cli_ep(client_endpoint),
  timeout(timeout), last_msg_time(high_resolution_timer::clock_type::now()),
  marked_for_deletion(false), server(server), acknowledgements(500),
  rate_obs_dur(get_duration(500e6)), last_ack(0), cur_message(0),
  data_exist(true), transition_probability(0.1),
  transition_threshold(RAND_MAX)
  {
    memset(send_buf, 0, sizeof(send_buf));
    socket.open(udp::v4());
    send_cnt = recv_cnt = 0;
    packet_size = 1472; //1500 bytes
    smallest_window = packet_size;
    rate = 8 * 5000; // 5kB/sec
    max_rate = 100e6; //100Mbps
    rtt_delay = 100000; //100ms
    time_gate = timestamp;
    tx_window = smallest_window;
    if (on_off_transitions)
      transition_threshold *= (1-transition_probability);
    send();
    data_received(timestamp, rcv, length);
  }
  
  ~udp_svr_client() {
    std::cout << "Client Terminating" << std::endl;
  }
  
  bool is_active() { return data_exist; }
  
  void data_received(const high_resolution_timer::time_point &timestamp,
                     const rcv_data& rcv, std::size_t length) {
    if (marked_for_deletion) return;
    
    //handle acknowledgements
    assert(length >= 5);
    int num_bytes = 0, ack_num = rcv.last_message_number;
    if (ack_num > last_ack) {
      num_bytes = (ack_num - last_ack) * packet_size;
      last_ack = ack_num;
    }
    acknowledgements.push_back(acknowledgment_info(num_bytes, timestamp));
    
    if (rcv.time_tick && rand() > transition_threshold) {
      data_exist = !data_exist;
      if (data_exist) {
        //will not send anything, but should be ready at the next timeout
        time_gate = high_resolution_timer::clock_type::now();
        send();
      }
    }
    
    //handle this message
    last_msg_time = timestamp;
    socket.async_receive_from(boost::asio::buffer(rcv_buf, sizeof(rcv_buf)),
                              cli_ep,
                              boost::bind(&udp_svr_client::handle_receive, this,
                                          _1, _2));
  }
  
  bool is_timed_out() {
    return (high_resolution_timer::clock_type::now() > last_msg_time + timeout);
  }
  
  bool is_marked_for_deletion() { return marked_for_deletion; }
  
  void stop() {
    socket.cancel();
    socket.close();
    timer.cancel();
    marked_for_deletion = true;
  }
  
  void update_rate(const client_info& info) {
    const int S = packet_size + 42;
    //estimate observed rate
    std::size_t buf_size = acknowledgements.size();
    if (buf_size == 0)
      return;
    
    high_resolution_timer::time_point cur_time;
    cur_time = high_resolution_timer::clock_type::now();
    std::int64_t pos = buf_size - 1;
    
    int sum_bytes = 0;
    while (pos >= 0 && cur_time - acknowledgements[pos].time < rate_obs_dur)
      sum_bytes += acknowledgements[pos--].num_bytes + 42;

    //To be correct, we must use the time from the earlier sample
    high_resolution_timer::duration dur;
    if (pos >= 0)
      dur = cur_time - acknowledgements[pos].time;
    else //here we are just starting, and we do not have enough samples
      dur = cur_time - acknowledgements[pos+1].time;
    
    float observed_rate = sum_bytes * 8e9 / dur.count();
    
    //estimate rate
    double tgt_rate = max_rate;
    for (int i = 0; i < info.num_switches; ++i) {
//      // The formula is
//      //            packet_size * capacity
//      // --------------------------------------------
//      //                     ( rate - observed_rate )
//      // packet_size + qbyte (----------------------)
//      //                     (         rate         )
//
//      double t = info.f_switches[i].rate - observed_rate;
//      t = (t > 0) ? t / info.f_switches[i].rate : 0;
//      double den = packet_size + info.f_switches[i].qbytes * t;
//      t = packet_size * info.f_switches[i].capacity / den;
//      if (t < tgt_rate) tgt_rate = t;
      double my_qbytes = info.f_switches[i].qbytes;
      if (info.f_switches[i].rate >= observed_rate &&
          info.f_switches[i].rate > 0)
        my_qbytes *= observed_rate / info.f_switches[i].rate;
      double rate = S * info.f_switches[i].capacity;
      rate /= (S + info.f_switches[i].qbytes - my_qbytes);
      if (rate < tgt_rate) tgt_rate = rate;
    }
    
    //estimate delay
    double delay = 0;
    for (int i = 0; i < info.num_switches; ++i) {
//      // Other bytes are
//      //       ( rate - observed_rate )
//      // qbyte (----------------------)
//      //       (         rate         )
//      // we add to it, the ratio of the tgt_rate to observed_rate multiplied
//      // by the packet size, which is not correct, but an approximation
//      double t = info.f_switches[i].rate - observed_rate;
//      t = (t > 0) ? t / info.f_switches[i].rate : 0;
//      double others_qbytes = t * info.f_switches[i].qbytes;
//      double new_qbytes = others_qbytes + packet_size;
      double other_qbytes = 0;
      if (info.f_switches[i].rate > observed_rate) {
        double myqbytes = observed_rate * info.f_switches[i].qbytes;
        myqbytes /= info.f_switches[i].rate;
        other_qbytes = info.f_switches[i].qbytes - myqbytes;
      }
      double new_qbytes = other_qbytes;
//      if (i == 0)
//        printf("other_qbytes = %lf, new_qbytes %lf, qbytes = %f\n",
//               other_qbytes, new_qbytes, info.f_switches[i].qbytes);
      
      delay += new_qbytes * 8e6 / info.f_switches[i].capacity;
      delay += info.f_switches[i].physical_delay;
    }
    for (int i = 0; i < info.num_switches; ++i) {
      delay += info.b_switches[i].qbytes * 8e6 / info.b_switches[i].capacity;
      delay += info.b_switches[i].physical_delay;
    }
    
    rate = tgt_rate * 1.05f;

    rtt_delay = static_cast<long long>(delay);
    tx_window = static_cast<int>(tgt_rate * delay / 8e6);
    if (tx_window < smallest_window) tx_window = smallest_window;
    double fractional_seconds_since_epoch
      = std::chrono::duration_cast<std::chrono::duration<double>>(
        std::chrono::system_clock::now().time_since_epoch()).count();
//    printf("Client = %p, %f, "
//           "observed_rate = %f, rate = %f, rtt_delay = %lld, tx_window = %d, "
//           "rate = %f\n",
//            this,
//            fractional_seconds_since_epoch,
//            observed_rate, rate, rtt_delay, tx_window, info.f_switches[0].rate);
  }
  
  const udp::endpoint& endpoint() { return cli_ep; }
  boost::asio::ip::address address() { return cli_ep.address(); }
  unsigned short port() { return cli_ep.port(); }
  
protected:
  void send() {
    if (marked_for_deletion || !data_exist) return;
    
    high_resolution_timer::time_point cur_time;
    cur_time = high_resolution_timer::clock_type::now();
    high_resolution_timer::duration one_packet_duration;
    one_packet_duration = get_duration(packet_size * 8e9 / rate);

    int count = 0;
    while (time_gate <= cur_time) {
      if ((cur_message - last_ack) * packet_size > tx_window) {
        time_gate = cur_time + one_packet_duration;
        break;
      }
      *(int *) send_buf = ++cur_message;
      socket.async_send_to(boost::asio::buffer(send_buf, packet_size),
                           cli_ep, boost::bind(&udp_svr_client::handle_send,
                                               this, _1, _2));
      time_gate += one_packet_duration;
      count++;
    }
    
    timer.expires_at(time_gate);
    timer.async_wait(boost::bind(&udp_svr_client::handle_timeout, this, _1));
  }
  
  void handle_receive(const error_code& ec, std::size_t length) {
    if (marked_for_deletion) return;
    if (length == sizeof(rcv_data))
      data_received(high_resolution_timer::clock_type::now(), rcv_buf, length);
    else
      printf("Incorrect message size was received, and will be ignored\n");
  }
  
  void handle_timeout(const boost::system::error_code& error) {
    if (error == boost::asio::error::operation_aborted)
      return;
    if (marked_for_deletion)
      return;
    if (data_exist)
      send();
  }
  
  void handle_send(const error_code& error, std::size_t bytes_transferred) {
    if (marked_for_deletion) return;
  }
  
protected:
  rcv_data rcv_buf;   //should be more than enough to hold a few bytes
  char send_buf[6144]; //should be more then enough to hold one packet
  int send_cnt, recv_cnt; //used to count how many bytes were received/sent
  int packet_size; //this is the tx packet size. It is most likely a const
  double rate, observed_rate, max_rate; //bits per second
  long long rtt_delay; //round trip delay in usec
  bool marked_for_deletion; //this objected is marked for deletion
  ack_buffer acknowledgements;
  high_resolution_timer::duration rate_obs_dur;
  int last_ack, cur_message;
  int tx_window, smallest_window;
  bool data_exist;
  const float transition_probability;
  float transition_threshold;
  
protected:
  high_resolution_timer::time_point last_msg_time, time_gate;
  high_resolution_timer::duration timeout;
  udp::socket socket;
  io_service& srvc;
  high_resolution_timer timer;
  udp::endpoint cli_ep; // client ip and port
  udp_server *server;
};

/////////////////////////////////////////////////////////////////////////////
class udp_server {
public:
  typedef std::map<udp::endpoint, udp_svr_client*> udp_clients_map;
  typedef std::pair<udp::endpoint, udp_svr_client*> udp_clients_pair;
  
  udp_server(io_service &service, sdn_manager *sdn, bool on_off_transitions)
  : srvc(service), socket(service), timer(service), sdn(sdn),
  on_off_transitions(on_off_transitions)
  {
    if (sdn) sdn->attach_server(this);
    socket.open(udp::v4());
  }
  
  ~udp_server() {
    std::cout << "Server terminating" << std::endl;
  }
  
  void start(const udp::endpoint& local_endpoint) {
    socket.bind(local_endpoint);
    socket.async_receive_from(boost::asio::buffer(rcv_buf, sizeof(rcv_buf)),
                              remote_ep,
                              boost::bind(&udp_server::handle_receive, this,
                                          _1, _2));
    timer.expires_from_now(get_duration(1e9)); //one second
    timer.async_wait(boost::bind(&udp_server::handle_timeout, this, _1));
  }
  
  void update_clients(const address& addr, const client_info& info) {
    //update more than one client if they exist
    udp_clients_map::iterator start = clients_map.begin();
    udp_clients_map::iterator end = clients_map.end();
    while ((start = find(start, end, addr)) != end) {
      start->second->update_rate(info);
      ++start;
    }
  }
  
  int get_active_clients() {
    if (!on_off_transitions) return -1;
    else {
      int num = 0;
      udp_clients_map::iterator it = clients_map.begin();
      for ( ;it != clients_map.end(); ++it)
        num += it->second->is_active() ? 1 : 0;
      return num;
    }
  }
  
protected:
  void handle_receive(const error_code& ec, std::size_t length);
  
//  void handle_send(const error_code& error, std::size_t bytes_transferred) {
//    //nothing much
//  }
  
  void handle_timeout(const boost::system::error_code& error) {
    if (error == boost::asio::error::operation_aborted)
      return;
    
    //if the client is not responding, remove it
    //To remove a client two steps are needed: stop it and in the next timeout
    // delete it.  Not sure if this can cause a problem if the client received
    // other events after it was deleted.
    udp_clients_map::iterator it = clients_map.begin();
    while (it != clients_map.end()) {
      if (it->second->is_timed_out()) {
        if (it->second->is_marked_for_deletion()) {
          address client_addr = it->second->address();
          delete it->second;
          clients_map.erase(it++);
          if (sdn) sdn->remove_client(client_addr);
        }
        else {
          it->second->stop();
          ++it;
        }
      }
      else
        ++it;
    }
    timer.expires_from_now(get_duration(1e9)); //one second
    timer.async_wait(boost::bind(&udp_server::handle_timeout, this, _1));
  }
  
protected:
  udp_clients_map::iterator
  find(udp_clients_map::iterator _start, udp_clients_map::iterator _end,
       const address& client_addr) {
    struct address_equal { //predicate
      address_equal(const address& addr) : _addr(addr) {}
      bool operator()( const udp_clients_pair& v) const {
        return v.second->address() == _addr;
      }
      address _addr;
    };
    return std::find_if(_start, _end, address_equal(client_addr));
  }
  
protected:
  rcv_data rcv_buf;   //should be more than enough to hold a few bytes
  
protected:
  udp_clients_map clients_map;
  io_service &srvc;
  udp::socket socket;
  high_resolution_timer timer;
  udp::endpoint remote_ep;
  bool on_off_transitions;
  
protected:
  sdn_manager *sdn;
};

#endif
