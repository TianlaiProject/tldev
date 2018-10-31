% Initial parameters.
f_start = 1605; % MHz
f_stop = 1705; % MHz
f_step = 5; % MHz
smoothing = 5; % 2^smoothing where smoothing is in [0, 1, ...,9]
% DUT_name = 'Amplifier-ZX60-33LN-S-Step10MHz';
% DUT_name = 'test_inst';
% DUT_name = 'NF-ZX60-33LN-S-Step10-10to4000_once';
DUT_name = '54LNAold1-3';
datafile_name = ['D:\\www\', DUT_name, '.txt'];
% cmd = 'poweron';
% cmd = 'calibration';
% cmd = 'work';
cmd = 'plot';


% smoothing:6->6.5s.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% dev = gpib('ni', 0, 8);
% dev = gpib('agilent', 0, 19);
% set(dev, 'InputBufferSize', 2500);
% fopen(dev);
% function dev = opendev(vendor, board_index, address)
% dev = gpib(vendor, board_index, address);
% set(dev, 'InputBufferSize', 2500);
% devid = fopen(dev);

if strcmp(cmd,'poweron')
    % Enter ENR table.
    % ENR for Agilent 346A 10MHz-18GHz Noise Source.    
    fprintf(dev, ['NR10MZ5.47EN100MZ5.56EN1000MZ5.37EN2000MZ5.41EN',...
        '3000MZ5.42EN4000MZ5.40EN5000MZ5.32EN6000MZ5.39EN7000MZ5.46EN',...
        '8000MZ5.39EN9000MZ5.53EN10000MZ5.62EN11000MZ5.51EN',...
        '12000MZ5.64EN13000MZ5.68EN14000MZ5.77EN15000MZ5.79EN',...
        '16000MZ5.91EN17000MZ5.84EN18000MZ5.40EN']);
    pause(1);
    % Special function sets (Fre, Gain, NF) output.
    fprintf(dev, 'SPH1');
elseif strcmp(cmd,'calibration')
    % Calibration.
    cali_cmd = ['M2FA',num2str(f_start),'MZFB',num2str(f_stop),'MZSS',num2str(f_step),'MZF',num2str(smoothing),'CA']
    fprintf(dev,cali_cmd);
elseif strcmp(cmd,'work')
    % Confirm Corrected NF and Gain.
    fprintf(dev, 'M2EN');
    pause(1);
    fid = fopen(datafile_name, 'at');
    % Get data.
%     fprintf(fid, '###########################################\n');
    for i=f_start:f_step:f_stop
        work_cmd = ['FR',num2str(i),'MZM2'];
        fprintf(dev,work_cmd);
        pause(6);
        fprintf(fid, fscanf(dev));
    end
    fclose(fid);
    NFdata = importdata(datafile_name, ',', 1);
    fig_gain = figure();
    plot(NFdata.data(:,1)./1e6, NFdata.data(:,2));
    grid on;
    xlabel('Frequency(MHz)');
    ylabel('Gain(dB)');
    title(['Gain of ', DUT_name]);
    print(fig_gain,'-dpng',['D:\\www\Gain_figure_',DUT_name,'.png']);
    fig_nf =  figure();
    plot(NFdata.data(:,1)./1e6,NFdata.data(:,3));
    grid on;
    xlabel('Frequency(MHz)');
    ylabel('Noise Figure(dB)');
    title(['Noise Figure of ', DUT_name]);
    print(fig_nf,'-dpng',['D:\\www\NF_figure_',DUT_name,'.png']);
elseif strcmp(cmd, 'plot')
    NFdata = importdata(datafile_name, ',', 1);
    fig_gain = figure();
    plot(NFdata.data(:,1)./1e6, NFdata.data(:,2));
    grid on;
%     ylim([5, 25]);
    xlabel('Frequency(MHz)');
    ylabel('Gain(dB)');
    title(['Gain of ', DUT_name]);
    print(fig_gain,'-dpng',['D:\\www\Gain_figure_',DUT_name,'.png']);
    fig_nf =  figure();
    plot(NFdata.data(:,1)./1e6, NFdata.data(:,3));
    grid on;
    ylim([0.0, 3]);
    xlabel('Frequency(MHz)');
    ylabel('Noise Figure(dB)');
    title(['Noise Figure of ', DUT_name]);
    print(fig_nf,'-dpng',['D:\\www\NF_figure_',DUT_name,'.png']);
end
% fclose(dev);
% delete(dev);
