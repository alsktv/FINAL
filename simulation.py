import sys
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 한글 폰트 설정 (Windows: Malgun Gothic / Mac: AppleGothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class COUPESimulatorApp:

  def __init__(self, root):
    self.root = root
    self.root.title(
        'TSMC COUPE 3D SoIC vs 2.5D μbump CPO Performance Simulator'
    )
    self.root.geometry('1520x960')
    self.root.configure(bg='#f4f6f9')

    # TTK 스타일 구성
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background='#f4f6f9')
    style.configure(
        'TLabelframe',
        background='#ffffff',
        font=('Malgun Gothic', 10, 'bold'),
    )
    style.configure(
        'TLabelframe.Label', background='#ffffff', foreground='#2c3e50'
    )
    style.configure('TLabel', background='#ffffff', font=('Malgun Gothic', 9))
    style.configure(
        'Accent.TButton',
        font=('Malgun Gothic', 10, 'bold'),
        background='#2980b9',
        foreground='white',
    )

    # 메인 레이아웃 (좌: 입력 및 수치 표, 우: 시각화 차트)
    left_panel = ttk.Frame(self.root, padding=10)
    left_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False)

    right_panel = ttk.Frame(self.root, padding=10)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # 1. 입력 패널 생성
    self.create_input_panel(left_panel)

    # 2. 결과 출력 표 생성
    self.create_result_panel(left_panel)

    # 3. 그래프 패널 생성 (그래프 하단 수식 + 변수 설명 칸 포함)
    self.create_chart_panel(right_panel)

    # 최초 1회 연산 및 바인딩
    self.auto_calculate_soic()
    self.run_simulation()

  def create_input_panel(self, parent):
    input_frame = ttk.LabelFrame(
        parent,
        text=' 1. 논문 파라미터 입력 (Paper Physics Inputs) ',
        padding=10,
    )
    input_frame.pack(fill=tk.X, pady=(0, 10))

    self.entries = {}

    # 1. 사용자 입력 파라미터 (2.5D μbump 기준)
    lbl_sec1 = ttk.Label(
        input_frame,
        text='--- 2.5D μbump (사용자 직접 입력) ---',
        font=('Malgun Gothic', 9, 'bold'),
        foreground='#2980b9',
    )
    lbl_sec1.grid(row=0, column=0, columnspan=2, sticky='w', pady=(2, 4))

    fields_mb = [
        ('μbump Pitch Length (μm)', 'mb_pitch', '40.0'),
        ('μbump Interconnect Cap (fF)', 'mb_c_int', '60.0'),
        ('μbump Unit Cell Density Ratio', 'mb_density', '1.0'),
    ]

    row = 1
    for label_text, var_name, default_val in fields_mb:
      lbl = ttk.Label(input_frame, text=label_text)
      lbl.grid(row=row, column=0, sticky='w', pady=2)
      entry = ttk.Entry(input_frame, width=12)
      entry.insert(0, default_val)
      entry.grid(row=row, column=1, sticky='e', pady=2)
      entry.bind('<KeyRelease>', lambda event: self.on_input_change())
      self.entries[var_name] = entry
      row += 1

    # 2. 자동 계산되는 파라미터 (3D TSMC SoIC - ReadOnly)
    lbl_sec2 = ttk.Label(
        input_frame,
        text='--- 3D TSMC SoIC (자동 연산 / Read-Only) ---',
        font=('Malgun Gothic', 9, 'bold'),
        foreground='#e74c3c',
    )
    lbl_sec2.grid(row=row, column=0, columnspan=2, sticky='w', pady=(8, 4))
    row += 1

    fields_soic = [
        ('SoIC Pitch Length (μm)', 'soic_pitch', '10.0'),
        ('SoIC Interconnect Cap (fF)', 'soic_c_int', '9.0'),
        ('SoIC Unit Cell Density Ratio', 'soic_density', '10.7'),
    ]

    for label_text, var_name, default_val in fields_soic:
      lbl = ttk.Label(input_frame, text=label_text)
      lbl.grid(row=row, column=0, sticky='w', pady=2)
      entry = ttk.Entry(input_frame, width=12, state='readonly')
      entry.grid(row=row, column=1, sticky='e', pady=2)
      self.entries[var_name] = entry
      row += 1

    # Unit Cell Density 물리적 의미 설명 팁 박스
    lbl_tip = ttk.Label(
        input_frame,
        text=(
            '※ Unit Cell Density: 단위 면적(mm²)당 배치 가능한\n   광'
            ' 변조기/소자(CPO Engine) 유닛 셀 집적 밀도 배율'
        ),
        font=('Malgun Gothic', 8),
        foreground='#555555',
        justify='left',
    )
    lbl_tip.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 4))
    row += 1

    # 3. 소자 및 회로 스펙 (Tx / Rx Circuit Specs)
    lbl_sec3 = ttk.Label(
        input_frame,
        text='--- Tx / Rx / Circuit Specifications ---',
        font=('Malgun Gothic', 9, 'bold'),
        foreground='#7f8c8d',
    )
    lbl_sec3.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 4))
    row += 1

    fields_specs = [
        ('Driver Output Res R_drv (Ω)', 'r_drv', '50.0'),
        ('Photodetector Cap C_PD (fF)', 'c_pd', '15.0'),
        ('PD Intrinsic Bandwidth (GHz)', 'pd_bw_int', '50.0'),
        ('Target Data Rate (Gbps)', 'data_rate', '50.0'),
    ]

    for label_text, var_name, default_val in fields_specs:
      lbl = ttk.Label(input_frame, text=label_text)
      lbl.grid(row=row, column=0, sticky='w', pady=2)
      entry = ttk.Entry(input_frame, width=12)
      entry.insert(0, default_val)
      entry.grid(row=row, column=1, sticky='e', pady=2)
      entry.bind('<KeyRelease>', lambda event: self.run_simulation())
      self.entries[var_name] = entry
      row += 1

    btn_run = ttk.Button(
        input_frame,
        text='시뮬레이션 실행 (Run Simulation)',
        style='Accent.TButton',
        command=self.run_simulation,
    )
    btn_run.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(8, 0))

  def on_input_change(self):
    """입력창에서 값을 타이핑할 때 SoIC 연산 및 차트 갱신 자동 수행"""
    self.auto_calculate_soic()
    self.run_simulation()

  def auto_calculate_soic(self):
    """마이크로 범프 입력 파라미터 변경 시 SoIC 파라미터 동적 자동 연산"""
    try:
      mb_pitch = float(self.entries['mb_pitch'].get())
      mb_c_int = float(self.entries['mb_c_int'].get())
      mb_density = float(self.entries['mb_density'].get())

      soic_pitch = mb_pitch * 0.25
      soic_c_int = mb_c_int * 0.15
      pitch_area_ratio = (mb_pitch / soic_pitch) ** 2
      soic_density = mb_density * (10.7 * (pitch_area_ratio / 16.0))

      for key, val in [
          ('soic_pitch', f'{soic_pitch:.1f}'),
          ('soic_c_int', f'{soic_c_int:.1f}'),
          ('soic_density', f'{soic_density:.1f}'),
      ]:
        entry = self.entries[key]
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, val)
        entry.config(state='readonly')
    except ValueError:
      pass

  def create_result_panel(self, parent):
    self.result_frame = ttk.LabelFrame(
        parent, text=' 2. 논문 실측 수치 대조표 및 상세 원리 ', padding=10
    )
    self.result_frame.pack(fill=tk.BOTH, expand=True)

    tree_container = ttk.Frame(self.result_frame)
    tree_container.pack(fill=tk.BOTH, expand=True)

    columns = ('metric', 'bump', 'soic', 'gain')
    self.tree = ttk.Treeview(
        tree_container, columns=columns, show='headings', height=14
    )

    self.tree.heading(
        'metric', text='성능 지표 / 상세 설명 (Metric & Description)'
    )
    self.tree.heading('bump', text='2.5D μbump')
    self.tree.heading('soic', text='3D SoIC')
    self.tree.heading('gain', text='실시간 계산 이득')

    self.tree.column('metric', width=310, minwidth=280, anchor='w')
    self.tree.column('bump', width=75, minwidth=60, anchor='center')
    self.tree.column('soic', width=75, minwidth=60, anchor='center')
    self.tree.column('gain', width=105, minwidth=80, anchor='center')

    v_scrollbar = ttk.Scrollbar(
        tree_container, orient=tk.VERTICAL, command=self.tree.yview
    )
    h_scrollbar = ttk.Scrollbar(
        tree_container, orient=tk.HORIZONTAL, command=self.tree.xview
    )
    self.tree.configure(yscroll=v_scrollbar.set, xscroll=h_scrollbar.set)

    self.tree.grid(row=0, column=0, sticky='nsew')
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar.grid(row=1, column=0, sticky='ew')

    tree_container.grid_rowconfigure(0, weight=1)
    tree_container.grid_columnconfigure(0, weight=1)

    self.tree.tag_configure(
        'main_row', font=('Malgun Gothic', 9, 'bold'), background='#ffffff'
    )
    self.tree.tag_configure(
        'desc_row',
        font=('Malgun Gothic', 8),
        background='#f8f9fa',
        foreground='#495057',
    )

  def create_chart_panel(self, parent):
    chart_frame = ttk.LabelFrame(
        parent,
        text=' 3. 비교 시각화 차트 (Visual Performance Analysis) ',
        padding=10,
    )
    chart_frame.pack(fill=tk.BOTH, expand=True)

    self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(
        2, 2, figsize=(9.0, 7.5), dpi=100
    )
    self.fig.patch.set_facecolor('#ffffff')

    self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
    self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

  def run_simulation(self):
    try:
      mb_pitch = float(self.entries['mb_pitch'].get())
      mb_c_int = float(self.entries['mb_c_int'].get())
      mb_density = float(self.entries['mb_density'].get())

      soic_pitch = float(self.entries['soic_pitch'].get())
      soic_c_int = float(self.entries['soic_c_int'].get())
      soic_density = float(self.entries['soic_density'].get())

      r_drv = float(self.entries['r_drv'].get())
      c_pd = float(self.entries['c_pd'].get())
      pd_bw_int = float(self.entries['pd_bw_int'].get())
      data_rate = float(self.entries['data_rate'].get())

    except ValueError:
      return

    # ---------------- 2. 동적 통합 물리 방정식 연산 ----------------
    c_tx_bump = mb_c_int + 10.0
    c_tx_soic = soic_c_int + 10.0

    c_rx_bump = c_pd + mb_c_int
    c_rx_soic = c_pd + soic_c_int

    iso_speed_bump = 1.0
    iso_speed_soic = np.sqrt(c_rx_bump / c_rx_soic)

    density_ratio = (mb_pitch / soic_pitch) ** 2 * (mb_density)
    bw_density_bump = mb_density * iso_speed_bump
    bw_density_soic = soic_density * iso_speed_soic
    total_bw_ratio = bw_density_soic / bw_density_bump

    tau_int = 1.0 / pd_bw_int if pd_bw_int > 0 else 0
    tau_rc_bump = 2 * np.pi * r_drv * (c_rx_bump * 1e-15) * 1e9
    tau_rc_soic = 2 * np.pi * r_drv * (c_rx_soic * 1e-15) * 1e9

    f3db_rx_bump = 1.0 / np.sqrt(tau_int**2 + tau_rc_bump**2)
    f3db_rx_soic = 1.0 / np.sqrt(tau_int**2 + tau_rc_soic**2)
    pd_bw_gain_pct = (f3db_rx_soic / f3db_rx_bump - 1.0) * 100.0

    noise_ratio_soic = (c_rx_soic / c_rx_bump) ** 2
    sens_gain_db = 10.0 * np.log10(1.0 / noise_ratio_soic)
    laser_power_saving_pct = (1.0 - noise_ratio_soic) * 100.0
    cap_saving_pct = (1.0 - soic_c_int / mb_c_int) * 100.0

    # ---------------- 3. 대조표(Treeview) 실시간 수치 갱신 ----------------
    for row in self.tree.get_children():
      self.tree.delete(row)

    items_with_multiline_desc = [
        (
            'Bond Pitch (μm)',
            f'{mb_pitch:.1f} μm',
            f'{soic_pitch:.1f} μm',
            f'<{soic_pitch/mb_pitch:.2f}x 축소',
            [
                '  └ Direct Cu-Cu Hybrid Bonding 적용으로',
                f'    Sub-{soic_pitch:.0f}μm 초미세 접합 달성',
            ],
        ),
        (
            'Interconnect Cap (fF)',
            f'{mb_c_int:.1f} fF',
            f'{soic_c_int:.1f} fF',
            f'-{cap_saving_pct:.1f}% 감축',
            [
                '  └ 범프 및 Underfill 완전 제거로',
                f'    배선 기생 용량 {cap_saving_pct:.1f}% 감축',
            ],
        ),
        (
            'MRM Unit Cell Density',
            f'{mb_density:.1f}x',
            f'{soic_density:.1f}x',
            f'>{soic_density/mb_density:.1f}x 증가',
            [
                '  └ 단위 면적(mm²)당 집적 가능한',
                (
                    f'    CPO 광 유닛 셀 개수'
                    f' {soic_density/mb_density:.1f}배 증대'
                ),
            ],
        ),
        (
            'Iso-power Data Speed',
            '1.0x',
            f'{iso_speed_soic:.2f}x',
            f'{iso_speed_soic:.2f}x 향상',
            [
                '  └ 동일 소모 전력 기준',
                f'    단일 광 채널 전송 속도 {iso_speed_soic:.2f}배 증가',
            ],
        ),
        (
            'Total BW Density Ratio',
            '1.0x',
            f'{total_bw_ratio:.1f}x',
            f'>{total_bw_ratio:.1f}x 향상',
            [
                (
                    f'  └'
                    f' [밀도({soic_density/mb_density:.1f}x) ×'
                    f' 속도({iso_speed_soic:.2f}x)]'
                ),
                f'    대역폭 밀도 {total_bw_ratio:.1f}배 폭증 연산',
            ],
        ),
        (
            'PD 3dB Bandwidth (GHz)',
            f'{f3db_rx_bump:.1f} GHz',
            f'{f3db_rx_soic:.1f} GHz',
            f'+{pd_bw_gain_pct:.1f}%',
            [
                '  └ 수신기 기생 용량 감축으로',
                (
                    f'    PD 대역폭 {f3db_rx_bump:.1f}G→{f3db_rx_soic:.1f}GHz'
                    ' 확장'
                ),
            ],
        ),
        (
            'TIA Noise Current Ratio',
            '1.00',
            f'{noise_ratio_soic:.2f}',
            f'-{(1.0-noise_ratio_soic)*100:.1f}%',
            [
                '  └ TIA 잡음 전류(Noise ∝ Cin²)',
                f'    입력 용량 감축으로 {(1.0-noise_ratio_soic)*100:.1f}% 절감',
            ],
        ),
        (
            'TIA Sensitivity Gain',
            '0.0 dB',
            f'+{sens_gain_db:.1f} dB',
            f'+{sens_gain_db:.1f} dB',
            [
                '  └ 수신기 잡음 전류 감소에 따른',
                f'    광 수신 감도 +{sens_gain_db:.1f}dBm 향상',
            ],
        ),
        (
            'Laser Power Saving',
            '0.0%',
            f'{laser_power_saving_pct:.1f}%',
            f'-{laser_power_saving_pct:.1f}%',
            [
                '  └ Rx 수신 감도 향상으로',
                f'    CPO 발광 레이저 전력 소모 {laser_power_saving_pct:.1f}% 절감',
            ],
        ),
    ]

    for metric, bump, soic, gain, desc_lines in items_with_multiline_desc:
      self.tree.insert(
          '', 'end', values=(metric, bump, soic, gain), tags=('main_row',)
      )
      self.tree.insert(
          '', 'end', values=(desc_lines[0], '', '', ''), tags=('desc_row',)
      )
      self.tree.insert(
          '', 'end', values=(desc_lines[1], '', '', ''), tags=('desc_row',)
      )

    # ---------------- 4. 동적 차트 시각화 & [수식 / 변수 설명] 분리 배치 ----------------
    self.ax1.clear()
    self.ax2.clear()
    self.ax3.clear()
    self.ax4.clear()

    # Subplot 1: Tx & Rx 기생 용량
    labels = ['Tx 용량 (fF)', 'Rx C_in 용량 (fF)']
    bump_caps = [c_tx_bump, c_rx_bump]
    soic_caps = [c_tx_soic, c_rx_soic]
    x = np.arange(len(labels))
    width = 0.35

    self.ax1.bar(
        x - width / 2, bump_caps, width, label='2.5D μbump', color='#95a5a6'
    )
    self.ax1.bar(
        x + width / 2, soic_caps, width, label='3D SoIC', color='#e74c3c'
    )
    self.ax1.set_xticks(x)
    self.ax1.set_xticklabels(labels, fontsize=8)
    self.ax1.set_title(
        f'기생 용량 감축 (-{cap_saving_pct:.0f}%)',
        fontsize=9.5,
        fontweight='bold',
    )
    self.ax1.legend(fontsize=7.5)
    self.ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # 1번 차트 하단: [좌 수식 / 우 변수 설명]
    eq1_text = (
        r'$C_{\mathrm{tx}} = C_{\mathrm{int}} + C_{\mathrm{pad}}$'
        '\n'
        r'$C_{\mathrm{rx}} = C_{\mathrm{PD}} + C_{\mathrm{int}}$'
    )
    var1_text = '• Cint: 배선 기생 용량\n• Cpd: PD 고유 접합 용량'

    self.ax1.text(
        0.26,
        -0.27,
        eq1_text,
        transform=self.ax1.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#f8f9fa',
            edgecolor='#bdc3c7',
            alpha=0.9,
        ),
    )
    self.ax1.text(
        0.75,
        -0.27,
        var1_text,
        transform=self.ax1.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#eef2f7',
            edgecolor='#34495e',
            alpha=0.9,
        ),
    )

    # Subplot 2: PD 3dB 대역폭 응답 곡선
    max_freq = max(data_rate * 1.5, f3db_rx_soic * 1.3)
    freqs = np.linspace(0, max_freq, 200)
    h_bump = 20 * np.log10(1 / np.sqrt(1 + (freqs / f3db_rx_bump) ** 2))
    h_soic = 20 * np.log10(1 / np.sqrt(1 + (freqs / f3db_rx_soic) ** 2))

    self.ax2.plot(freqs, h_bump, 'r--', label='μbump Curve')
    self.ax2.plot(freqs, h_soic, 'b-', label='SoIC Curve')
    self.ax2.axhline(-3, color='gray', linestyle=':', alpha=0.7)

    self.ax2.axvline(
        f3db_rx_bump,
        color='red',
        linestyle=':',
        alpha=0.7,
        label=f'μbump f_3dB ({f3db_rx_bump:.1f}GHz)',
    )
    self.ax2.axvline(
        f3db_rx_soic,
        color='blue',
        linestyle=':',
        alpha=0.7,
        label=f'SoIC f_3dB ({f3db_rx_soic:.1f}GHz)',
    )

    self.ax2.set_xlabel('주파수 (GHz)', fontsize=8)
    self.ax2.set_ylabel('응답 (dB)', fontsize=8)
    self.ax2.set_title(
        'PD 3dB 대역폭 가변 응답', fontsize=9.5, fontweight='bold'
    )
    self.ax2.legend(fontsize=6.5, loc='lower left')
    self.ax2.grid(True, linestyle='--', alpha=0.5)

    # 2번 차트 하단: [좌 수식 / 우 변수 설명]
    eq2_text = (
        r'$f_{\mathrm{3dB}} = \frac{1}{\sqrt{(1/f_{\mathrm{int}})^2 + (2\pi'
        r' R_{\mathrm{drv}} C_{\mathrm{rx}})^2}}$'
    )
    var2_text = '• f_int: PD 고유 대역폭\n• R_drv: 드라이버 저항'

    self.ax2.text(
        0.30,
        -0.27,
        eq2_text,
        transform=self.ax2.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#f8f9fa',
            edgecolor='#bdc3c7',
            alpha=0.9,
        ),
    )
    self.ax2.text(
        0.78,
        -0.27,
        var2_text,
        transform=self.ax2.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#eef2f7',
            edgecolor='#34495e',
            alpha=0.9,
        ),
    )

    # Subplot 3: 잡음 전류 & 레이저 전력 절감
    rx_metrics = ['잡음 전류 비율', '레이저 전력 소모']
    bump_rx_vals = [1.0, 1.0]
    soic_rx_vals = [noise_ratio_soic, 1.0 - (laser_power_saving_pct / 100.0)]

    x3 = np.arange(len(rx_metrics))
    self.ax3.bar(
        x3 - width / 2, bump_rx_vals, width, label='2.5D μbump', color='#95a5a6'
    )
    self.ax3.bar(
        x3 + width / 2, soic_rx_vals, width, label='3D SoIC', color='#2ecc71'
    )
    self.ax3.set_xticks(x3)
    self.ax3.set_xticklabels(rx_metrics, fontsize=8)
    self.ax3.set_title(
        f'잡음 전류 & 레이저 절감 (-{(1-noise_ratio_soic)*100:.0f}%)',
        fontsize=9.5,
        fontweight='bold',
    )
    self.ax3.legend(fontsize=7.5)
    self.ax3.grid(axis='y', linestyle='--', alpha=0.5)

    # 3번 차트 하단: [좌 수식 / 우 변수 설명]
    eq3_text = (
        r'$\mathrm{Noise\ Ratio} = (C_{\mathrm{rx,SoIC}} /'
        r' C_{\mathrm{rx,bump}})^2$'
        '\n'
        r'$\mathrm{Laser\ Saving} \propto (1 - \mathrm{Noise\ Ratio})$'
    )
    var3_text = '• Noise: TIA 적분 잡음\n• Sensitivity: 광 수신감도'

    self.ax3.text(
        0.30,
        -0.27,
        eq3_text,
        transform=self.ax3.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#f8f9fa',
            edgecolor='#bdc3c7',
            alpha=0.9,
        ),
    )
    self.ax3.text(
        0.78,
        -0.27,
        var3_text,
        transform=self.ax3.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#eef2f7',
            edgecolor='#34495e',
            alpha=0.9,
        ),
    )

    # Subplot 4: 총 대역폭 밀도 향상 배율
    bw_labels = ['2.5D μbump', '3D TSMC SoIC']
    bw_values = [bw_density_bump, total_bw_ratio]
    colors = ['#7f8c8d', '#2980b9']

    bars = self.ax4.bar(bw_labels, bw_values, color=colors, width=0.45)
    self.ax4.set_ylabel('대역폭 밀도 배율 (x)', fontsize=8)
    self.ax4.set_title(
        f'총 대역폭 밀도 ({total_bw_ratio:.1f}x 향상)',
        fontsize=9.5,
        fontweight='bold',
    )
    self.ax4.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
      yval = bar.get_height()
      self.ax4.text(
          bar.get_x() + bar.get_width() / 2.0,
          yval,
          f'{yval:.1f}x',
          ha='center',
          va='bottom',
          fontweight='bold',
          fontsize=8.5,
      )

    # 4번 차트 하단: [좌 수식 / 우 변수 설명]
    eq4_text = (
        r'$\mathrm{Total\ BW\ Density} = \left(\frac{\mathrm{Pitch}_{\mathrm{bump}}}{\mathrm{Pitch}_{\mathrm{soic}}}\right)^2'
        r' \times \sqrt{\frac{C_{\mathrm{rx,bump}}}{C_{\mathrm{rx,soic}}}}$'
    )
    var4_text = '• Pitch: 범프 결합 피치\n• Speed: Iso-power 속도'

    self.ax4.text(
        0.33,
        -0.27,
        eq4_text,
        transform=self.ax4.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#f8f9fa',
            edgecolor='#bdc3c7',
            alpha=0.9,
        ),
    )
    self.ax4.text(
        0.80,
        -0.27,
        var4_text,
        transform=self.ax4.transAxes,
        ha='center',
        va='top',
        fontsize=7.5,
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='#eef2f7',
            edgecolor='#34495e',
            alpha=0.9,
        ),
    )

    self.fig.tight_layout()
    self.fig.subplots_adjust(
        bottom=0.20, hspace=0.52
    )  # 하단 수식+변수 박스 공간 확충
    self.canvas.draw()


if __name__ == '__main__':
  root = tk.Tk()
  app = COUPESimulatorApp(root)
  root.mainloop()