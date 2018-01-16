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

#define METHOD 2

/////////////////////////////////////////////////////////////////////////////
struct rcv_data {
  rcv_data() : last_message_number(0), time_tick(false) {}
  operator char *() const { return (char *)this; }
  int last_message_number;
  bool time_tick;
  long long time_stamp;
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
  marked_for_deletion(false), server(server),
  rate_obs_dur(get_duration(500e6)), last_ack(0), cur_message(0),
  data_exist(true), transition_probability(0.1),
  transition_threshold(RAND_MAX),
  last_obs_rate_update_time(high_resolution_timer::clock_type::now()),
  observed_rate(0.0f), num_rec_bytes(0), running_counter(0)
  {
    memset(send_buf, 0, sizeof(send_buf));
    socket.open(udp::v4());
    send_cnt = recv_cnt = 0;
    packet_size = 1472; //1500 bytes
    smallest_window = packet_size;
    tx_rate = 8 * 5000; // 5kB/sec
    max_rate = 100e6; //100Mbps
    rtt_delay = 100000; //100ms
    time_gate = timestamp;
    tx_window = smallest_window;
    if (on_off_transitions)
      transition_threshold *= (1-transition_probability);
    send();
    data_received(timestamp, rcv, length);
#if METHOD == 1
    skip_count = 200;
#endif
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
      num_bytes = (ack_num - last_ack) * (packet_size + 42);
      last_ack = ack_num;
    }
    num_rec_bytes += num_bytes;
    
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
  
  //////////////////////////////////////////////////////////////////////////////
//   void update_rate(const client_info& info, bool forward) {
//   
//     if (!forward)
//       return;
//     
//     // The formula is
//     //            packet_size * capacity
//     // --------------------------------------------
//     //                     ( rate - observed_rate )
//     // packet_size + qbyte (----------------------)
//     //                     (         rate         )
//     
//     const int S = packet_size + 42;
//     const float tgt_rate_factor = 1.25f;
//     const float processing_delay = 100e6; //100ms
//     
//     high_resolution_timer::time_point cur_time;
//     cur_time = high_resolution_timer::clock_type::now();
//     if (forward && (++running_counter & 0x1) == 0)
//     {
//       float dt = (cur_time - last_obs_rate_update_time).count() / 1e9f;
//       float alpha = std::min(1.0f, sdn_switch::tau * dt);
//       float rate = num_rec_bytes * 8.0f / dt;
//       observed_rate += alpha * (rate - observed_rate);
//       num_rec_bytes = 0;
//       last_obs_rate_update_time = cur_time;
//     }
//     
//     //estimate rate
//     double tgt_rate = max_rate;
//     double physical_delay = 0, queuing_delay = 0;
//     int bottleneck_switch_index = 0;
//     double bn_bar = 0.0f, bn_hat = 0.0f, bn_lambda_ratio = 1.0f;
//     for (int i = 0; i < info.num_switches; ++i) {
//       
//       //most recent
//       double y_hat = observed_rate;
//       double y_bar = info.f_switches[i].rate;
//       double q_bar_actual = info.f_switches[i].qbytes;
//       q_bar_actual = (info.f_switches[i].qbytes + std::min(y_bar / (y_hat + 0.000001), 4.0)) / 2;
//       double q_hat_actual = q_bar_actual;
//       if (y_bar >= y_hat && y_bar > 0)
//         q_hat_actual *= y_hat / y_bar;
//       
//       //remove prediction
//       double q_bar_delayed = q_bars[i].get_delayed_val();
//       double q_hat_delayed = q_hats[i].get_delayed_val();
//       double q_bar_error = q_bar_actual - q_bar_delayed;
//       double q_hat_error = q_hat_actual - q_hat_delayed;
//       
//       //add recent val
//       double q_bar = q_bar_error + q_bars[i].get_recent_val();
//       double q_hat = q_hat_error + q_hats[i].get_recent_val();
//             
//       double rate = S * info.f_switches[i].capacity;
//       rate /= (S + std::max(q_bar - q_hat, 0.0));
//       
//       if (rate < tgt_rate) { 
//         tgt_rate = rate; 
//         bottleneck_switch_index = i; 
//         bn_bar = q_bar_actual;
//         bn_hat = q_hat_actual;
// //         if (y_bar >= y_hat && y_bar > 0) {
//           bn_lambda_ratio = q_bar_actual / S;
// //           if (i == 1) printf("%f\n", bn_lambda_ratio);
// //         }
// //         else
// //           bn_lambda_ratio = 1.0f;
//       }
//       
// //       if (i == 1)
// //         printf("%5f %5f %5f %5f %5f %5f %f\n", q_bar_delayed, q_hat_delayed,
// //            q_bar_actual, q_hat_actual, q_bar_error, q_hat_error, rate);
// //         printf("%5f %5f %5f %5f %5f %5f %f\n", q_bar_actual, q_hat_actual,
// //            q_bar_error, q_hat_error, q_bar, q_hat, rate);
//       
//       //Time for information to show on switch and get feedback
//       //This should exclude the physical delay of this switch
//       double switch_delay = physical_delay * 1000 + (i+1) * processing_delay;
//       q_hats[i].set_delay(switch_delay, cur_time);
//       q_bars[i].set_delay(switch_delay, cur_time);
// //       q_hats[i].set_delay(info.f_switches[i].info_delay, cur_time);
// //       q_bars[i].set_delay(info.f_switches[i].info_delay, cur_time);
//       
//       //time delay
//       double other_qbytes = q_bar_actual - q_hat_actual;
//       queuing_delay += (S + other_qbytes) * 8e6 / info.f_switches[i].capacity;
//       queuing_delay += info.b_switches[i].qbytes * 8e6 / info.b_switches[i].capacity;
//       physical_delay += info.f_switches[i].physical_delay;
//       physical_delay += info.b_switches[i].physical_delay;
//     }
//     
//     for (int i = 0; i < info.num_switches; ++i) {
//       high_resolution_timer::time_point last_time;
//       last_time = q_hats[i].get_recent_time();
//       float dt = (cur_time - last_time).count() / 1e9f; //in seconds
//       float alpha = std::min(1.0f, sdn_switch::tau * dt);
//       float q_bar = q_bars[i].get_recent_val();
//       float q_hat = q_hats[i].get_recent_val();
// 
//       if (bottleneck_switch_index == i) {
//         q_bar += alpha * (S * bn_lambda_ratio - q_bar);
//         q_bar = std::max(q_bar, 0.0f);
//         q_hat += alpha * (S - q_hat);
//         q_hat = std::max(q_hat, 0.0f);
// //         printf("%f %f %f ", q_bar, q_hat, bn_lambda_ratio);
// //         printf("%f %f\n", q_bars[i].get_delayed_val(), q_hats[i].get_delayed_val());
//       }
//       else {
//         q_bar *= alpha;
//         q_hat *= alpha;        
//       }
//       q_bars[i].push_back(q_bar, cur_time);
//       q_hats[i].push_back(q_hat, cur_time);
//     }    
//     
//     tx_rate = tgt_rate * tgt_rate_factor;
//     double delay = physical_delay + queuing_delay;
//     tx_window = static_cast<int>(tgt_rate * delay / 8e6);
//     if (tx_window < smallest_window) tx_window = smallest_window;
//   }

#if METHOD == 1
  //////////////////////////////////////////////////////////////////////////////
  void update_rate(const client_info& info, bool forward) {
    
    if (!forward)
        return;
        
    const int S = packet_size + 42;
    const float tgt_rate_factor = 1.00f;

    // The formula is
    //            packet_size * capacity
    // --------------------------------------------
    //                     ( rate - observed_rate )
    // packet_size + qbyte (----------------------)
    //                     (         rate         )

    // estimate my rate
    high_resolution_timer::time_point cur_time;
    cur_time = high_resolution_timer::clock_type::now();
    if (forward && (++running_counter & 0x1) == 0)
    {

      float dt = (cur_time - last_obs_rate_update_time).count() / 1e9f;
      float alpha = std::min(1.0f, sdn_switch::tau * dt);
      float rate = num_rec_bytes * 8.0f / dt;
      observed_rate += alpha * (rate - observed_rate);
      num_rec_bytes = 0;
      last_obs_rate_update_time = cur_time;
    }
    
    //estimate new rate
    double tgt_rate = max_rate;
    double physical_delay = 0, queuing_delay = 0;
    int btn_switch = 0;
    for (int i = 0; i < info.num_switches; ++i) {
      
      double y_hat = observed_rate;
      double y_bar = info.f_switches[i].rate;
      double q_bar = info.f_switches[i].qbytes;
      double C = info.f_switches[i].capacity;
      
      double my_qbytes = q_bar;
      if (y_bar >= y_hat && y_bar > 0)
        my_qbytes *= y_hat / y_bar;
      
      double rate = S * C;
      rate /= (S + q_bar - my_qbytes);
      if (rate < tgt_rate) { tgt_rate = rate; btn_switch = i; }
      
      //time delay
      double other_qbytes = q_bar - my_qbytes;
      queuing_delay += (S + other_qbytes) * 8e6 / C;
      queuing_delay += info.b_switches[i].qbytes * 8e6 / C;
      physical_delay += info.f_switches[i].physical_delay;
      physical_delay += info.b_switches[i].physical_delay;
    }
    
    //find window size
    double delay = physical_delay + queuing_delay;
    int temp_tx_window = static_cast<int>(tgt_rate * delay / 8e6);
    if (temp_tx_window < smallest_window) temp_tx_window = smallest_window;
    
    double fractional_seconds_since_epoch
      = std::chrono::duration_cast<std::chrono::duration<double>>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    printf("%f %d ", fractional_seconds_since_epoch, temp_tx_window);
    
    //implement a smith predictor
    if (skip_count) 
      --skip_count;
    else
      temp_tx_window += old_W.get_recent_val() - old_W.get_delayed_val();
    
    printf("%s %d %d %d ", skip_count == 0 ? "T":"F", temp_tx_window, 
           old_W.get_recent_val(), old_W.get_delayed_val());
    
    //process data for next smith predictor
    //dw
    int dq = temp_tx_window - tx_window;
    
    //dw into linearised model of G, which is
    //C.D.S/(S+(1-y_hat/y_bar).q_bar)
    //the linearised model is
    double y_hat = observed_rate;
    double y_bar = info.f_switches[btn_switch].rate;
    y_bar = std::min(y_bar, y_hat);
    double others_portion = 1;
    if (y_bar >= y_hat && y_bar > 0)
      others_portion = 1 - y_hat / y_bar;
    double q_bar = info.f_switches[btn_switch].qbytes;
    double C = info.f_switches[btn_switch].capacity;    
    double num = (C/8) * (delay/1e6) * S * others_portion;
    double den = (S + others_portion * q_bar) * (S + others_portion * q_bar);
    double dw = num * dq / den;
    
    printf("dq=%d dw=%f ", dq, dw);
    
    //accumulator
    old_W.set_delay(physical_delay * 1000, cur_time);
    int new_W = static_cast<int>(old_W.get_recent_val() + dw + 0.5);
    old_W.push_back(new_W, cur_time);
    
    //calculate rates
    tx_window = temp_tx_window;
    tx_rate = tx_window * tgt_rate_factor * 8e6 / delay;
    
    printf("%d %f\n", tx_window, tx_rate);
    
//     for (int i = 0; i < info.num_switches; ++i) {
//       double y_hat = observed_rate;
// //       y_hat -= info.f_switches[i].y_hat.get_delayed_val();
// //       y_hat += info.f_switches[i].y_hat.get_recent_val();
// //       y_hat = y_hat > 0 ? y_hat : 0.0;
//       double y_bar = info.f_switches[i].rate;
// //       y_bar -= info.f_switches[i].y_bar.get_delayed_val();
// //       y_bar += info.f_switches[i].y_bar.get_recent_val();
// //       y_bar = y_bar > 0 ? y_bar : 0.0;
//       double q_bar = info.f_switches[i].qbytes;
// //       q_bar -= info.f_switches[i].q_bar.get_delayed_val();
// //       q_bar += info.f_switches[i].q_bar.get_recent_val();
// //       q_bar = q_bar > 0 ? q_bar : 0.0;
//             
// //       if (i == 0)
// //         printf("%f\n", y_hat);
// //       if (i == 0)
// //         printf("%f %f %f\n", y_hat, y_bar, q_bar);    
//     
//       info.f_switches[i].y_hat.set_delay(physical_delay);
//       
//       float y_hat = info.f_switches[i].y_hat.get_recent_val();
//       high_resolution_timer::time_point y_hat_time;
//       y_hat_time = info.f_switches[i].y_hat.get_recent_time();
//       info.f_switches[i].y_hat.push_back(rate, cur_time);
//       
//       float y_bar = info.f_switches[i].rate - y_hat + rate;
//       y_bar = y_bar > 0 ? y_bar : 0.0f;
//       info.f_switches[i].y_bar.push_back(y_bar, cur_time);
//       
//       float dr = y_bar - info.f_switches[i].capacity;
//       float qbytes = info.f_switches[i].qbytes;
//       qbytes += dr * (cur_time - y_hat_time).count() / 1e9f;
//       qbytes = qbytes > 0.0f ? qbytes : 0.0f;
//       info.f_switches[i].q_bar.push_back(qbytes, cur_time);
//       
//       printf("%f %f %f\n", rate, y_bar, qbytes);
//     }
//     printf("raet: %f %f %f\n", info.f_switches[0].rate, info.f_switches[1].rate, info.f_switches[2].rate);
  }
#endif

#if METHOD == 2
  //////////////////////////////////////////////////////////////////////////////
  void update_rate(const client_info& info, bool forward) {
  
    if (!forward)
        return;
        
    const int S = packet_size + 42;
    const float tgt_rate_factor = 1.00f;
    const double info_delay[3] = {0.025, 0.3, 0.5};
    if (forward && (++running_counter & 0x1) == 0)
    {
      high_resolution_timer::time_point cur_time;
      cur_time = high_resolution_timer::clock_type::now();
      float dt = (cur_time - last_obs_rate_update_time).count() / 1e9f;
      float alpha = std::min(1.0f, sdn_switch::tau * dt);
      float rate = num_rec_bytes * 8.0f / dt;
      observed_rate += alpha * (rate - observed_rate);
      num_rec_bytes = 0;
      last_obs_rate_update_time = cur_time;
    }
    
    //estimate rate
    double tgt_rate = max_rate;
    double physical_delay = 0, queuing_delay = 0;
    for (int i = 0; i < info.num_switches; ++i) {
      
      double y_hat = observed_rate;
      double y_bar = info.f_switches[i].rate;
      double q_bar = info.f_switches[i].qbytes;
      double C = info.f_switches[i].capacity;
      
      double my_qbytes = q_bar;
      if (y_bar >= y_hat && y_bar > 0)
        my_qbytes *= y_hat / y_bar;

      double rate = S * C;
      rate /= (S + q_bar - my_qbytes);
      double t = 2*S * 8 / info_delay[i]; //rate change in bits per second
      double upper_rate = y_hat * C / y_bar + t + std::max((C - y_bar) * y_bar / y_hat, 0.0);
      double lower_rate = std::max(y_hat * C / y_bar - (my_qbytes - S + 2*S) * 8 / info_delay[i], 0.0);
      rate = std::max(rate, lower_rate);
      rate = std::min(rate, upper_rate);
//       if (i == 1) printf("%f %f %f %f %f %f %s %f %s\n", my_qbytes, 
//       y_hat, y_bar, C, rate, 
//       upper_rate, rate==upper_rate?"T":"F", lower_rate, rate==lower_rate?"T":"F");
      
      if (rate < tgt_rate) tgt_rate = rate;
      
      //time delay
      double other_qbytes = q_bar - my_qbytes;
      queuing_delay += (S + other_qbytes) * 8e6 / C;
      queuing_delay += info.b_switches[i].qbytes * 8e6 / C;
      physical_delay += info.f_switches[i].physical_delay;
      physical_delay += info.b_switches[i].physical_delay;
    }

    tx_rate = tgt_rate * tgt_rate_factor;
    double delay = physical_delay + queuing_delay;
    tx_window = static_cast<int>(tgt_rate * delay / 8e6);
    if (tx_window < smallest_window) tx_window = smallest_window;
  }
#endif

#if METHOD == 3
  //////////////////////////////////////////////////////////////////////////////
  void update_rate(const client_info& info, bool forward) {
  
    if (!forward)
        return;
        
    const int S = packet_size + 42;
    const float tgt_rate_factor = 1.00f;
    if (forward && (++running_counter & 0x1) == 0)
    {
      high_resolution_timer::time_point cur_time;
      cur_time = high_resolution_timer::clock_type::now();
      float dt = (cur_time - last_obs_rate_update_time).count() / 1e9f;
      float alpha = std::min(1.0f, sdn_switch::tau * dt);
      float rate = num_rec_bytes * 8.0f / dt;
      observed_rate += alpha * (rate - observed_rate);
      num_rec_bytes = 0;
      last_obs_rate_update_time = cur_time;
    }
    
    //estimate rate
    double tgt_rate = max_rate;
    double physical_delay = 0, queuing_delay = 0;
    for (int i = 0; i < info.num_switches; ++i) {
      
      double y_hat = observed_rate;
      double y_bar = info.f_switches[i].rate;
      double q_bar = info.f_switches[i].qbytes;
      double C = info.f_switches[i].capacity;
      
      double my_qbytes = q_bar;
      if (y_bar >= y_hat && y_bar > 0)
        my_qbytes *= y_hat / y_bar;

      double rate = S * C;
      rate /= (S + q_bar - my_qbytes);      
      if (rate < tgt_rate) tgt_rate = rate;
      //time delay
      double other_qbytes = q_bar - my_qbytes;
      queuing_delay += (S + other_qbytes) * 8e6 / C;
      queuing_delay += info.b_switches[i].qbytes * 8e6 / C;
      physical_delay += info.f_switches[i].physical_delay;
      physical_delay += info.b_switches[i].physical_delay;
    }

    tx_rate = tgt_rate * tgt_rate_factor;
    double delay = physical_delay + queuing_delay;
    tx_window = static_cast<int>(tgt_rate * delay / 8e6);
    if (tx_window < smallest_window) tx_window = smallest_window;
  }
#endif


  const udp::endpoint& endpoint() { return cli_ep; }
  boost::asio::ip::address address() { return cli_ep.address(); }
  unsigned short port() { return cli_ep.port(); }
  
protected:
  void send() {
    if (marked_for_deletion || !data_exist) return;
    
    high_resolution_timer::time_point cur_time;
    cur_time = high_resolution_timer::clock_type::now();
    high_resolution_timer::duration one_packet_duration;
    one_packet_duration = get_duration((packet_size + 42) * 8e9 / tx_rate);

    int count = 0;
    while (time_gate <= cur_time) {
      if ((cur_message - last_ack) * (packet_size + 42) > tx_window) {
        time_gate = cur_time + one_packet_duration;
        break;
      }
      *(int *) send_buf = ++cur_message;
      *(long long *)(((int *) send_buf) + 4) = cur_time.time_since_epoch().count();
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
  double tx_rate, max_rate; //bits per second
  long long rtt_delay; //round trip delay in usec
  bool marked_for_deletion; //this objected is marked for deletion
  high_resolution_timer::duration rate_obs_dur;
  int last_ack, cur_message;
  int tx_window, smallest_window;
  bool data_exist;
  const float transition_probability;
  float transition_threshold;
  
protected:
  int num_rec_bytes; //used to count a number of packets, only count when
                   //there is a time gap larger than 0.05s
  double observed_rate;
  high_resolution_timer::time_point last_obs_rate_update_time;
  int running_counter;
#if METHOD == 1
  int skip_count;
  circular_buf_with_delay<int> old_W;
#endif
  
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
  
  void update_clients(const address& addr, const client_info& info, bool forward) {
    //update more than one client if they exist
    udp_clients_map::iterator start = clients_map.begin();
    udp_clients_map::iterator end = clients_map.end();
    while ((start = find(start, end, addr)) != end) {
      start->second->update_rate(info, forward);
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
