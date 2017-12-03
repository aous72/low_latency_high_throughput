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
matlab2tikz('realistic_rate.tikz');

close all;
clearvars;
server = dlmread('./results1/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
matlab2tikz('realistic_queue.tikz');

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
matlab2tikz('unrealistic_rate.tikz');

close all;
clearvars;
server = dlmread('./results2/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
matlab2tikz('unrealistic_queue.tikz');

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
matlab2tikz('poor_rate.tikz');

close all;
clearvars;
server = dlmread('./results3/11/server_data_file_0.txt');
server(:,1) = server(:,1) - server(1,1);
plot(server(1:927,1), server(1:927,6) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
matlab2tikz('poor_queue_1.tikz');

close all;
clearvars;
sw = dlmread('./results3/12/s4-eth2.txt');
sw(:,1) = sw(:,1) - sw(1,1);
plot(sw(515:end,1)-51.4, sw(515:end,2) / 1000);
xlabel('Time in seconds');
ylabel('Number of Queued Bytes in kB');
matlab2tikz('poor_queue_2.tikz');
