CC=gcc
CFLAGS=-O2 -std=gnu++11 -I.
SVR_DEPS = server.h sdn_manager.h  
SVR_OBJ = server.o sdn_manager.o  
CLNT_OBJ = client.o  
LIBS = -lm -lstdc++ -lboost_system -lpthread

%.o: %.cpp $(SVR_DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

all: server client

server: $(SVR_OBJ)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

client: $(CLNT_OBJ)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean: 
	rm *.o client server

