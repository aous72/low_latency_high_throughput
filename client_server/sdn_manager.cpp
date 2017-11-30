//
//  sdn_manager.cpp
//  client_server
//
//  Created by Aous Naman on 12/03/2015.
//  Copyright (c) 2015 Aous Naman. All rights reserved.
//

#include "sdn_manager.h"
#include "server.h"

/////////////////////////////////////////////////////////////////////////////
high_resolution_timer::duration get_duration(double nanosecs) {
  double t = round(nanosecs);
  return high_resolution_timer::duration(static_cast<int_least64_t>(t));
}

const float sdn_switch::alpha = 0.1f;

/////////////////////////////////////////////////////////////////////////////
int sdn_manager::process_replies() {
  int num_replies = 0;
  while (ebuf.get_size()) {
    char *p = ebuf.get_buf();
//     printf("%s\n", p);
    int pos = 0, body_size = 0;
    //eatup the header
    while (pos + 2 < ebuf.get_size() && (p[0] != '\r' || p[1] != '\n')) {
      if (pos+17 < ebuf.get_size() && strncmp(p, "Content-Length: ", 16)==0) {
        body_size = atoi(p + 16);
        //          std::cout << "Content-length: " << body_size << std::endl;
      }
      while (pos < ebuf.get_size() && *p != '\n') { ++p; ++pos; }
      if (pos < ebuf.get_size() && *p == '\n')  { ++p; ++pos; };
    }
    if (body_size > 0 && pos + 2 + body_size <= ebuf.get_size()) {
      assert(p[0] == '\r' && p[1] == '\n');
      pos += 2; p += 2;
      //        ebuf.get_buf()[pos + body_size] = 0;
      //        std::cout << ebuf.get_buf() + pos << std::endl;
      // the message is processed here
      address client_addr = requests.front().addr;
      client_properties::iterator it;
      it = find(clients.begin(), clients.end(), client_addr);
      if (it != clients.end()) {
        it->second->process_message(ebuf.get_buf() + pos, body_size,
                                    requests.front().forward,
                                    server->get_active_clients());
        server->update_clients(client_addr, *(it->second));
        requests.erase(requests.begin());
      }
      else
        requests.erase(requests.begin()); //the client disappeared
      
      //remove the message
      ebuf.remove_data(pos + body_size);
      ++num_replies;
    }
    else
      break;
  }
  return num_replies;
}
