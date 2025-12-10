import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';
import ChatBot from '../components/ChatBot';
import ForceGraph from '../components/ForceGraph';
import './EasyMode.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const EasyMode = () => {
    const [portfolio, setPortfolio] = useState([]);
    const [dailyReport, setDailyReport] = useState("");
    const [guruAnalyses, setGuruAnalyses] = useState({});
    const [guruInfos, setGuruInfos] = useState({});
    const [loading, setLoading] = useState(false);
    const [selectedGuru, setSelectedGuru] = useState("Warren Buffett");
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [newStockCode, setNewStockCode] = useState("");
    const [newStockAmount, setNewStockAmount] = useState("");
    const [addError, setAddError] = useState("");
    const [dataStatus, setDataStatus] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    const user = localStorage.getItem('user') || "20201651";

    useEffect(() => {
        fetchPortfolio();
        fetchGraphData();
        fetchDataStatus();
    }, []);

    useEffect(() => {
        if (portfolio.length > 0) {
            fetchGraphData();
        }
    }, [portfolio.length]);

    const fetchDataStatus = async () => {
        try {
            const res = await axios.get('http://localhost:8000/api/data/status');
            setDataStatus(res.data);
        } catch (err) {
            console.error("Failed to fetch data status", err);
        }
    };

    const handleRefreshData = async () => {
        setRefreshing(true);
        try {
            await axios.post('http://localhost:8000/api/data/refresh');
            await fetchDataStatus();
            await fetchPortfolio();
        } catch (err) {
            console.error("Failed to refresh data", err);
        } finally {
            setRefreshing(false);
        }
    };

    const fetchPortfolio = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/easy/portfolio?user=${user}`);
            setPortfolio(res.data.portfolio);
            setDailyReport(res.data.daily_report || "");
        } catch (err) {
            console.error("Failed to fetch portfolio", err);
        }
    };

    const handleAddStock = async () => {
        if (!newStockCode || !newStockAmount) return;
        setAddError("");
        try {
            const res = await axios.post('http://localhost:8000/api/easy/portfolio/add', {
                user: user,
                stock: {
                    code: newStockCode,
                    amount: parseInt(newStockAmount),
                    name: "" // Backend will find name
                }
            });

            if (res.data.status === 'error') {
                setAddError(res.data.message);
                return;
            }

            setNewStockCode("");
            setNewStockAmount("");
            fetchPortfolio();
        } catch (err) {
            console.error("Failed to add stock", err);
            setAddError("종목 추가 중 오류가 발생했습니다.");
        }
    };
    const handleRemoveStock = async (code) => {
        const stock = portfolio.find(p => p.code === code);
        if (!stock) return;

        const amountStr = window.prompt(`삭제할 수량을 입력하세요. (현재 보유: ${stock.amount}주)\n전체 삭제를 원하시면 ${stock.amount}를 입력하거나 취소를 누르세요.`, stock.amount);

        if (amountStr === null) return; // Cancelled

        const amount = parseInt(amountStr);
        if (isNaN(amount) || amount <= 0) {
            alert("유효한 수량을 입력해주세요.");
            return;
        }

        try {
            const res = await axios.post('http://localhost:8000/api/easy/portfolio/remove', {
                user: user,
                code: code,
                amount: amount
            });

            if (res.data.status === 'success') {
                fetchPortfolio();
            } else {
                alert("삭제 실패: " + res.data.message);
            }
        } catch (err) {
            console.error("Failed to remove stock", err);
            alert("삭제 중 오류가 발생했습니다.");
        }
    };

    const fetchGraphData = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/easy/graph?user=${user}`);
            setGraphData(res.data);
        } catch (err) {
            console.error("Failed to fetch graph data", err);
        }
    };

    const handleGuruAnalyze = async () => {
        setLoading(true);
        try {
            const res = await axios.post('http://localhost:8000/api/easy/guru-analysis', {
                guru: selectedGuru,
                portfolio: portfolio
            });
            setGuruAnalyses(prev => ({
                ...prev,
                [selectedGuru]: res.data.analysis
            }));
            setGuruInfos(prev => ({
                ...prev,
                [selectedGuru]: res.data.guru_info
            }));
        } catch (err) {
            console.error("Analysis failed", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container easy-mode">
            <header className="page-header">
                <div className="header-main">
                    <h1>나만의 포트폴리오</h1>
                    <p>AI 대가들의 조언을 받아보세요.</p>
                </div>
                <div className="data-status-bar">
                    {dataStatus && (
                        <>
                            <span className="status-text">
                                📊 데이터 갱신: {dataStatus.price_data?.last_update === "Never"
                                    ? "갱신 필요"
                                    : dataStatus.price_data?.last_update}
                            </span>
                            <button
                                className="btn btn-sm"
                                onClick={handleRefreshData}
                                disabled={refreshing}
                            >
                                {refreshing ? "갱신 중..." : "🔄 새로고침"}
                            </button>
                        </>
                    )}
                </div>
            </header>

            <div className="grid-2">
                <div className="card portfolio-section">
                    <h2>보유 종목</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={portfolio}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {portfolio.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <ul className="stock-list">
                        {portfolio.map((item, idx) => (
                            <li key={item.code} className="stock-item">
                                <span className="color-dot" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                                <div className="stock-info">
                                    <span className="stock-name">{item.name}</span>
                                    <span className="stock-details">
                                        현재가 {item.current_price?.toLocaleString()}원 × {item.amount}주
                                    </span>
                                    <span className="stock-purchase">
                                        매수가 {item.purchase_price?.toLocaleString()}원
                                    </span>
                                </div>
                                <div className="stock-value-container">
                                    <span className="stock-value">{item.value?.toLocaleString()}원</span>
                                    <span className={`stock-change ${item.change_rate >= 0 ? 'positive' : 'negative'}`}>
                                        {item.change_rate >= 0 ? '+' : ''}{(item.change_rate * 100)?.toFixed(2)}%
                                    </span>
                                    <span className={`stock-profit ${item.profit_loss >= 0 ? 'positive' : 'negative'}`}>
                                        {item.profit_loss >= 0 ? '+' : ''}{item.profit_loss?.toLocaleString()}원
                                    </span>
                                    <button
                                        className="btn-delete"
                                        onClick={() => handleRemoveStock(item.code)}
                                        title="종목 삭제"
                                        style={{ marginLeft: '10px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem' }}
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="card guru-section">
                    <h2>대가의 조언 (Guru Analysis)</h2>
                    <div className="guru-selector">
                        {["Warren Buffett", "Mark Minervini", "Charlie Munger"].map(guru => (
                            <button
                                key={guru}
                                className={`chip ${selectedGuru === guru ? 'active' : ''}`}
                                onClick={() => setSelectedGuru(guru)}
                            >
                                {guru === "Warren Buffett" ? "워렌 버핏" :
                                    guru === "Mark Minervini" ? "마크 미너비니" : "찰리 멍거"}
                            </button>
                        ))}
                    </div>

                    {/* Guru Info Card */}
                    {guruInfos[selectedGuru] && (
                        <div className="guru-info-card">
                            <div className="guru-profile">
                                <img
                                    src={guruInfos[selectedGuru].image}
                                    alt={guruInfos[selectedGuru].korean_name}
                                    className="guru-image"
                                />
                                <div className="guru-text">
                                    <h3>{guruInfos[selectedGuru].korean_name}</h3>
                                    <p className="guru-desc">{guruInfos[selectedGuru].description}</p>
                                </div>
                            </div>
                            <div className="guru-focus">
                                <strong>🔍 중점 분석 포인트:</strong>
                                <ul>
                                    {guruInfos[selectedGuru].focus_areas.map((area, idx) => (
                                        <li key={idx}>{area}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}

                    <div className="analysis-box">
                        {loading ? (
                            <div className="loading-container">
                                <div className="loading-spinner"></div>
                                <p>대가의 생각을 읽는 중...</p>
                            </div>
                        ) : guruAnalyses[selectedGuru] ? (
                            <div className="analysis-text">
                                <ReactMarkdown>{guruAnalyses[selectedGuru]}</ReactMarkdown>
                            </div>
                        ) : (
                            <div className="placeholder">
                                <p>포트폴리오를 분석하여 투자 인사이트를 얻으세요.</p>
                                <button className="btn btn-primary" onClick={handleGuruAnalyze} style={{ margin: '0 auto', display: 'block' }}>분석 시작</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="card report-section" style={{ marginTop: '20px' }}>
                <h2>📈 오늘의 맞춤 리포트</h2>
                <div className="report-content">
                    {dailyReport ? (
                        <ReactMarkdown>{dailyReport}</ReactMarkdown>
                    ) : (
                        <p>포트폴리오를 등록하면 맞춤 리포트가 제공됩니다.</p>
                    )}
                </div>
            </div>

            <div className="card input-section" style={{ marginTop: '20px' }}>
                <h2>➕ 보유 종목 추가 (Add Holding Stock)</h2>
                <div className="input-form" style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                        <input
                            type="text"
                            placeholder="종목코드 또는 종목명 (예: 삼성전자)"
                            value={newStockCode}
                            onChange={(e) => setNewStockCode(e.target.value)}
                            style={{ padding: '10px', borderRadius: '4px', border: addError ? '1px solid #ef4444' : '1px solid #ddd', width: '100%' }}
                        />
                        {addError && <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '4px' }}>{addError}</p>}
                    </div>
                    <input
                        type="number"
                        placeholder="수량"
                        value={newStockAmount}
                        onChange={(e) => setNewStockAmount(e.target.value)}
                        style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ddd', width: '100px' }}
                    />
                    <button className="btn btn-secondary" onClick={handleAddStock}>추가</button>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '5px' }}>* 종목명(예: 삼성전자) 또는 코드(예: 005930)로 검색 가능합니다.</p>
            </div>

            <div className="card graph-section">
                <h2>종목 관계도 (Correlation Graph)</h2>
                <p className="desc">내 종목과 주가 흐름이 유사한 기업들을 확인하세요.</p>
                <div className="graph-container" style={{ height: '500px' }}>
                    <ForceGraph
                        nodes={graphData.nodes}
                        links={graphData.links}
                        myStockCodes={portfolio.map(p => p.code)}
                    />
                </div>
            </div>
            <ChatBot />
        </div>
    );
};

export default EasyMode;
