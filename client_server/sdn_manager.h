//
//  sdn_manager.h
//  client_server
//
//  Created by Aous Naman on 12/03/2015.
//  Copyright (c) 2015 Aous Naman. All rights reserved.
//

#ifndef client_server_sdn_manager_h
#define client_server_sdn_manager_h

#include <cstdio>
#include <iostream>

#include <map>
#include <list>

#include <boost/bind.hpp>

#include <boost/asio/high_resolution_timer.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/ip/udp.hpp>
#include <boost/asio/ip/tcp.hpp>

using boost::asio::io_service;
using boost::asio::high_resolution_timer;
using boost::asio::ip::udp;
using boost::asio::ip::tcp;
using boost::asio::ip::address;
using boost::system::error_code;

class udp_server;

const int max_switches = 5;

/////////////////////////////////////////////////////////////////////////////
high_resolution_timer::duration get_duration(double nanosecs);

/////////////////////////////////////////////////////////////////////////////
struct sdn_switch
{
  sdn_switch() {
    rate = 0;
    qbytes = 0;
    capacity = 1000000.0f; //1Mbps
    physical_delay = 0;
  }
  
  void add_reading(float delta, int tbytes, int qbytes,
                   float capacity, long long physical_delay,
                   FILE *data_file = NULL, int number_active_clients = -1)
  {
//     assert(delta != 0);
    if (delta == 0)
      return;
    float cur_rate = tbytes * 8.0f / delta;
    float cur_alpha = min(1,0f, alpha * delta);
    this->rate += cur_alpha * (cur_rate - this->rate);
    this->qbytes += cur_alpha * (qbytes - this->qbytes);
    this->capacity = capacity;
    this->physical_delay = physical_delay;
    if (data_file) {
      fprintf(data_file, "%f %f", cur_rate, this->rate);
      fprintf(data_file, " %d %f", qbytes, this->qbytes);
      if (number_active_clients >= 0)
        fprintf(data_file, " %d", number_active_clients);
      fprintf(data_file, "\n");
      fflush(data_file);
    }

//    printf("tbytes = %d, qbytes = %d, capacity = %f, physical_delay = %lld\n",
//           tbytes, qbytes, capacity, physical_delay);
  }
  
  float rate;                 //rate through the switch in bps
  float qbytes;               //bytes in queue
  //the following are usually constants
  float capacity;             //bps
  long long physical_delay;   //usec
  
  static const float alpha;
};

/////////////////////////////////////////////////////////////////////////////
struct client_info {
  client_info()
  : count(1), fidx(-1), bidx(-1), num_switches(-1), data_file(NULL)
  {
    data_file = fopen("server_data_file.txt", "wt");
  }
  
  ~client_info() {
    fclose(data_file);
  }
  
  void process_message(const char *buf, std::size_t remaining_chars,
                       bool forward, int num_active_clients) {
//    assert(buf[0] == '\[');
    if (buf[0] != '\[') {
      char tb[10240];
      strncpy(tb, buf, remaining_chars);
      tb[remaining_chars] = 0;
      printf("%s\n", tb);
      assert(0);
    }
    // skip the first '\['
    --remaining_chars; ++buf;
    
    while (remaining_chars > 0 && *buf == '\[')
    {
      int idx, num_switches;
      float delta;
      // idx as int
      // delta as float in seconds, the time between this and the last reading
      if (sscanf(buf, "[%d, %d", &idx, &num_switches) != 2) {
        std::cerr << "error in sdn response format\n";
        printf("%s\n", buf);
      }
      else {
        //skip one comma
        while (remaining_chars > 0 && *buf != ',')
        { --remaining_chars; ++buf; }
        --remaining_chars; ++buf;
//         while (remaining_chars > 0 && *buf != ',')
//         { --remaining_chars; ++buf; }
//         --remaining_chars; ++buf;
      }
      if (num_switches > max_switches)
        std::cerr << "unsupported number of switches\n";
      else
        this->num_switches = num_switches;
      for (int i = 0; i < num_switches; ++i)
      {
//        if (forward) printf("forward switch %d\n", i);
//        else printf("backward switch %d\n", i);
        //skip one coma
        while (remaining_chars > 0 && *buf != ',')
        { --remaining_chars; ++buf; }
        --remaining_chars; ++buf;
        
        int delta;
        int qbytes, transmitted_bytes;
        int capacity, physical_delay;
        if (sscanf(buf, "%d, %d, %d, %d, %d", &qbytes, &transmitted_bytes,
                   &capacity, &physical_delay, &delta) != 5) {
          std::cerr << "error in switch reading format\n";
          printf("%s\n", buf);
        }
        if (forward) {
          if (idx >= fidx) {
            fidx = idx;
            f_switches[i].add_reading(delta / 1000.0f, transmitted_bytes, qbytes,
                                      capacity * 1000.0f,
                                      (std::int64_t)(physical_delay*1000),
                                      i==0 ? data_file : NULL,
                                      num_active_clients);
//            printf("fsw %d, q = %f, r = %f, c = %f, d = %lld\n", i,
//                   f_switches[i].qbytes, f_switches[i].rate,
//                   f_switches[i].capacity, f_switches[i].physical_delay);
//            printf("forward %d %d\n", idx, i);
          }
        }
        else {
          if (idx >= bidx) {
            bidx = idx;
            b_switches[i].add_reading(delta / 1000.0f, transmitted_bytes, qbytes,
                                      capacity * 1000.0f,
                                      (std::int64_t)(physical_delay*1000));
//            printf("bsw %d, q = %f, r = %f, c = %f, d = %lld\n", i,
//                   b_switches[i].qbytes, b_switches[i].rate,
//                   b_switches[i].capacity, b_switches[i].physical_delay);
//            printf("backward %d %d\n", idx, i);
          }
        }

        //skip four commas
        for (int t = 0; t < 4; ++t) {
          while (remaining_chars > 0 && *buf != ',')
          { --remaining_chars; ++buf; }
          --remaining_chars; ++buf;
        }
//        buf[remaining_chars] = 0;
//        printf("%s\n", buf);
      }
      
      // find the closing bracket
      while (remaining_chars > 0 && *buf != ']')
      { --remaining_chars; ++buf; }
      //find the next bracket
      while (remaining_chars > 0 && *buf != '\[')
      { --remaining_chars; ++buf; }
    }
  }
  
  int count; //number of clients at this address
  int num_switches;
  int fidx, bidx;
  sdn_switch f_switches[max_switches], b_switches[max_switches];
  
protected:
  FILE *data_file;
};

/////////////////////////////////////////////////////////////////////////////
struct request_info {
  request_info() : forward(true) {}
  explicit request_info(const address& addr, bool forward)
  : addr(addr), forward(forward) {}
  
  address addr;
  bool forward;
};

/////////////////////////////////////////////////////////////////////////////
struct expandable_buffer {
  expandable_buffer() : buf(NULL), size(0), allocated_storage(0) {
    allocated_storage = 16384;
    buf = new char[allocated_storage];
  }
  ~expandable_buffer() { if (buf) delete[] buf; }
  
  char *get_buf() { return buf; }
  std::size_t get_size() { return size; }
  
  void add_data(char *data, std::size_t data_size) {
    if (data_size + size + 1 > allocated_storage) {
      while (data_size + size + 1 > allocated_storage)
        allocated_storage = allocated_storage * 3 / 2;
      char *tp = buf;
      buf = new char[allocated_storage];
      memcpy(buf, tp, size);
      delete[] tp;
    }
    memcpy(buf + size, data, data_size);
    buf[size + data_size] = 0;
    size += data_size;
  }
  
  void remove_data(int data_size) {
    assert(data_size <= size);
    char *dp = buf; const char *sp = buf + data_size;
    for (std::size_t repeat = size - data_size; repeat > 0; --repeat)
      *dp++ = *sp++;
    *dp = 0;
    size -= data_size;
  }
  
  void clear() {
    size = 0;
  }
  
  char *buf;
  std::size_t size;
  std::size_t allocated_storage;
};

/////////////////////////////////////////////////////////////////////////////
class sdn_manager {
public:
  typedef std::pair<const address, client_info*> client_pair;
  typedef std::map<const address, client_info*> client_properties;
  typedef std::list<request_info> requests_list;
  
  sdn_manager(io_service& service, tcp::endpoint sdn_endpoint,
              const address& local_addr, double nanosecond_timeout)
  : srvc(service), socket(service), timer(service), sdn_ep(sdn_endpoint),
  local_addr(local_addr), ns_timeout(nanosecond_timeout), server(NULL),
  connected(false), ns_request_interval(50e6), send_buf(NULL) {
    send_buf_size = 8192;
    send_buf = new char[send_buf_size];
    try_connect();
  }
  
  ~sdn_manager() {
    if (send_buf) delete[] send_buf;
    socket.cancel();
    socket.close();
    std::cout << "SDN Client Terminating" << std::endl;
  }
  
  void register_client(const address& client) {
    client_properties::iterator it;
    it = find(clients.begin(), clients.end(), client);
    if (it != clients.end())
      ++(it->second->count);
    else
      clients.insert(client_pair(client, new client_info));
  }

  void remove_client(const address& client) {
    client_properties::iterator it;
    it = find(clients.begin(), clients.end(), client);
    if (it != clients.end()) {
      if (--it->second->count == 0) {
        delete it->second;
        clients.erase(it);
      }
    }
    else
      assert(0);
  }
  
  void attach_server(udp_server *server) {
    assert(this->server == NULL);
    this->server = server;
  }
  
protected:
  void try_connect() {
    connected = false;
    timer.cancel();
    socket.close();
    requests.clear();
    ebuf.clear();
    
    std::cout << "Sdn trying to connect" << std::endl;    
    socket.open(tcp::v4());
    socket.async_connect(sdn_ep, boost::bind(&sdn_manager::handle_connect,
                                             this, _1));
    timer.expires_from_now(get_duration(ns_timeout));
    timer.async_wait(boost::bind(&sdn_manager::handle_timeout, this, _1));
  }
  
  void request_wait() {
    if (clients.size() && requests.size() == 0) {
      send_buf[0] = 0;
      client_properties::iterator it;
      for (it = clients.begin(); it != clients.end(); ++it) {
        char t_buf[1024];
        sprintf(t_buf,
                "GET /stats/%s/%s/%d/0/ HTTP/1.1\r\nHost: localhost\r\n\r\n"
                "GET /stats/%s/%s/%d/0/ HTTP/1.1\r\nHost: localhost\r\n\r\n",
                local_addr.to_string().c_str(),
                it->first.to_string().c_str(),
                it->second->fidx >= 0 ? it->second->fidx : 0,
                it->first.to_string().c_str(),
                local_addr.to_string().c_str(),
                it->second->bidx >= 0 ? it->second->bidx : 0);
        std::size_t needed_space = strlen(send_buf) + strlen(t_buf) + 1;
        if (needed_space > send_buf_size) {
          while (needed_space > send_buf_size)
            send_buf_size = send_buf_size * 3 / 2;
          char *t = send_buf;
          send_buf = new char[send_buf_size];
          strcpy(send_buf, t);
          delete[] t;
        }
        strcat(send_buf, t_buf);
//        printf("%s\n", send_buf);
        requests.push_back(request_info(it->first, true));
        requests.push_back(request_info(it->first, false));
      }
      socket.async_send(boost::asio::buffer(send_buf, strlen(send_buf)),
                        boost::bind(&sdn_manager::handle_send, this,
                                    _1, _2));
      socket.async_receive(boost::asio::buffer(recv_buf),
                           boost::bind(&sdn_manager::handle_receive, this,
                                       _1, _2));
    }
    timer.expires_from_now(get_duration(ns_request_interval));
    timer.async_wait(boost::bind(&sdn_manager::handle_timeout, this, _1));
  }
  
  void handle_connect(const boost::system::error_code& error) {
    if (!error) {
      timer.cancel();
      std::cout << "Sdn connected" << std::endl;
      connected = true;
      request_wait();
    }
    else {
      std::cout << "Sdn not connected :" << error.message() << std::endl;
      try_connect();
    }
  }
  
  void handle_timeout(const boost::system::error_code& error) {
    if (error == boost::asio::error::operation_aborted)
      return;
    
    if (!connected)
      try_connect();
    else
      request_wait();
  }
  
  void handle_receive(const boost::system::error_code& error,
                      std::size_t bytes_transferred) {
    if (error == boost::asio::error::eof ||
        error == boost::asio::error::connection_reset) {
      std::cout << "Sdn connection lost: " << error.message() << std::endl;
      try_connect();
    }
    else {
      //do other stuff here
//      std::cout << "bytes received = " << bytes_transferred << std::endl;
      ebuf.add_data(recv_buf, bytes_transferred);
      process_replies();
      if (requests.size() > 0)
        socket.async_receive(boost::asio::buffer(recv_buf),
                             boost::bind(&sdn_manager::handle_receive, this,
                                         _1, _2));
    }
  }

  void handle_send(const boost::system::error_code& error,
                   std::size_t bytes_transferred) {
    //nothing to do really
  }
  
  int process_replies();
  
protected:
  client_properties::iterator
  find(client_properties::iterator _start, client_properties::iterator _end,
       const address& val) const {
    struct address_equal { //predicate
      address_equal(const address& addr) : _addr(addr) {}
      bool operator()( const client_pair& v) const {
        return v.first == _addr;
      }
      address _addr;
    };
    return std::find_if(_start, _end, address_equal(val));
  }
  
protected:
  char *send_buf, recv_buf[8192];
  std::size_t send_buf_size;
  expandable_buffer ebuf;
  client_properties clients;
  requests_list requests; //a list of requests to keep track of the replies
  //each send increments it by 2, and each double bracket decrement is by 1
  //async_receive needs to be called whenever outstanding_requestts_counter
  //is more than -1, effectively let it linger after all the data has been
  //received
  udp_server *server;
  tcp::socket socket;
  io_service& srvc;
  high_resolution_timer timer;
  tcp::endpoint sdn_ep; //sdn_server address and port
  address local_addr; //local address
  const double ns_timeout, ns_request_interval;
  bool connected; //true when the connection is established and usable
};

#endif /* defined(client_server_sdn_manager_h) */
