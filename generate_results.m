addpath('/Users/aous/Documents/MATLAB/matlab2tikz/src');

%% first set of results
close all;
clearvars;
client1 = dlmread('./results1/14/client_data.txt');
client1(:,1) = client1(:,1) - client1(1,1);
client1(:,2) = client1(:,2) * 1500 * 8 / 0.1;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2)) / 1e6)
hold on
client2 = dlmread('./results1/12/client_data.txt');
client2(:,1) = client2(:,1) - client2(1,1);
client2(:,2) = client2(:,2) * 1500 * 8 / 0.1;
plot([zeros(180,1);client2(1:771,1)] + 18, filtfilt([1 1 1], 3, [zeros(180,1);client2(1:771,2)]) / 1e6);
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('realistic_rate.tikz');

close all;
clearvars;
server = dlmread('./results1/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('realistic_queue.tikz');

%% second set of results
close all;
clearvars;
client1 = dlmread('./results2/14/client_data.txt');
client1(:,1) = client1(:,1) - client1(1,1);
client1(:,2) = client1(:,2) * 1500 * 8 / 0.1;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2)) / 1e6)
hold on
client2 = dlmread('./results2/12/client_data.txt');
client2(:,1) = client2(:,1) - client2(1,1);
client2(:,2) = client2(:,2) * 1500 * 8 / 0.1;
plot([zeros(176,1);client2(1:830,1)] + 17.6, filtfilt([1 1 1], 3, [zeros(176,1);client2(1:830,2)]) / 1e6);
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('unrealistic_rate.tikz');

close all;
clearvars;
server = dlmread('./results2/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('unrealistic_queue.tikz');

%% third set of results
close all;
clearvars;
client1 = dlmread('./results3/14/client_data.txt');
client1(:,1) = client1(:,1) - client1(1,1);
client1(:,2) = client1(:,2) * 1500 * 8 / 0.1;
plot(client1(1:1000,1), filtfilt([1 1 1], 3, client1(1:1000,2)) / 1e6)
hold on
client2 = dlmread('./results3/13/client_data.txt');
client2(:,1) = client2(:,1) - client2(1,1);
client2(:,2) = client2(:,2) * 1500 * 8 / 0.1;
plot([zeros(191,1);client2(1:830,1)] + 19.1, filtfilt([1 1 1], 3, [zeros(191,1);client2(1:830,2)]) / 1e6);
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('poor_rate.tikz');

close all;
clearvars;
server = dlmread('./results3/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('poor_queue_1.tikz');

close all;
clearvars;
sw = dlmread('./results3/12/s4-eth2.txt');
sw(:,1) = sw(:,1) - sw(1,1);
plot(sw(515:end,1)-51.4, sw(515:end,2) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('poor_queue_2.tikz');

%% result for Figure 12, taken from results6
close all;
clearvars;
client1 = dlmread('./results6/14/client_data.txt');
client2 = dlmread('./results6/12/client_data.txt'); % client 2 starts first
start_time = client1(1,1);
client1(:,1) = client1(:,1) - start_time;
client2(:,1) = client2(:,1) - start_time;
figure;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2) * 1514 * 8 / 1e5));
hold on
plot(client2(:,1), filtfilt([1 1 1], 3, client2(:,2) * 1514 * 8 / 1e5));
grid
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('figure12_rate.tikz');

clear client1 client2
server = dlmread('./results6/11/server_data_file_0.txt');
server(:,1) = server(:,1) - start_time;
figure;
plot(server(:,1), server(:,6) / 1000);
hold on
plot(server(:,1), filter(0.1, [1, -0.9], server(:,6) / 1000));
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure12_queue.tikz');

%% result for Figure 13, taken from results7
close all;
clearvars;
client1 = dlmread('./results7/14/client_data.txt');
client2 = dlmread('./results7/13/client_data.txt'); % client 2 starts first
start_time = client1(1,1);
client1(:,1) = client1(:,1) - start_time;
client2(:,1) = client2(:,1) - start_time;
figure;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2) * 1514 * 8 / 1e5));
hold on
plot(client2(:,1), filtfilt([1 1 1], 3, client2(:,2) * 1514 * 8 / 1e5));
grid
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('figure13_rate.tikz');

clear client1 client2
server = dlmread('./results7/11/server_data_file_0.txt');
server(:,1) = server(:,1) - start_time;
figure;
plot(server(:,1), server(:,7) / 1000);
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure13_queue1.tikz');

figure;
plot(server(:,1), server(:,14) / 1000);
hold on
plot(server(:,1), filter(0.1, [1, -0.9], server(:,14) / 1000));
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure13_queue2.tikz');

%% result for Figure 14, taken from results4
close all;
clearvars;
client1 = dlmread('./results4/14/client_data.txt');
client2 = dlmread('./results4/13/client_data.txt'); % client 2 starts first
start_time = client1(1,1);
client1(:,1) = client1(:,1) - start_time;
client2(:,1) = client2(:,1) - start_time;
figure;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2) * 1514 * 8 / 1e5));
hold on
plot(client2(:,1), filtfilt([1 1 1], 3, client2(:,2) * 1514 * 8 / 1e5));
grid
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('figure14_rate.tikz');

clear client1 client2
server = dlmread('./results4/11/server_data_file_0.txt');
server(:,1) = server(:,1) - start_time;
figure;
plot(server(:,1), filter(0.1, [1, -0.9], server(:,6) / 1000));
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure14_queue1.tikz');

figure;
plot(server(:,1), server(:,14) / 1000);
hold on
% server(1:589,15) = 0;
% server(1031:end,15) = 0;
% plot(server(:,1), server(:,15) / 1000);
plot(server(:,1), filter(0.1, [1, -0.9], server(:,14) / 1000));
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure14_queue2.tikz');

%% result for Figure 15, taken from results5
close all;
clearvars;
f = './results5/';
client1 = dlmread([f '14/client_data.txt']);
client2 = dlmread([f '13/client_data.txt']); % client 2 starts first
start_time = client1(1,1);
client1(:,1) = client1(:,1) - start_time;
client2(:,1) = client2(:,1) - start_time;
figure;
plot(client1(:,1), filtfilt([1 1 1], 3, client1(:,2) * 1514 * 8 / 1e5));
hold on
plot(client2(:,1), filtfilt([1 1 1], 3, client2(:,2) * 1514 * 8 / 1e5));
grid
xlabel('Time in seconds');
ylabel('Bandwidth in Mbps');
% matlab2tikz('figure15_rate.tikz');

clear client1 client2
server = dlmread([f '11/server_data_file_0.txt']);
server(:,1) = server(:,1) - start_time;
figure;
plot(server(:,1), server(:,7) / 1000);
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure15_queue1.tikz');

figure;
plot(server(:,1), server(:,14) / 1000);
hold on
plot(server(:,1), filter(0.1, [1, -0.9], server(:,14) / 1000));
grid
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
% matlab2tikz('figure15_queue2.tikz');
