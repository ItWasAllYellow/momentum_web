import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './ExpertMode.css';

const ExpertMode = () => {
    const [stocks, setStocks] = useState([]);
    const [toneChanges, setToneChanges] = useState([]);
    const [toneWatchList, setToneWatchList] = useState([]);
    const [activeTab, setActiveTab] = useState('all'); // 'all' or 'tone'
    const [loading, setLoading] = useState(false);
    const [selectedNewsStock, setSelectedNewsStock] = useState(null);
    const [stockNews, setStockNews] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [newWatchCode, setNewWatchCode] = useState('');

    // Keyword search states
    const [keywordInput, setKeywordInput] = useState('');
    const [stockKeywords, setStockKeywords] = useState([]);
    const [keywordSearchResults, setKeywordSearchResults] = useState(null);
    const [searchingKeyword, setSearchingKeyword] = useState(false);

    const user = localStorage.getItem('user') || "20201651";

    useEffect(() => {
        fetchStocks();
        fetchToneChanges();
        fetchToneWatchList();
    }, []);

    const fetchStocks = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/api/expert/stocks');
            setStocks(res.data);
        } catch (err) {
            console.error("Failed to fetch stocks", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchToneChanges = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/expert/tone-changes?user=${user}`);
            setToneChanges(res.data);
        } catch (err) {
            console.error("Failed to fetch tone changes", err);
        }
    };

    const fetchToneWatchList = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/expert/tone-watch?user=${user}`);
            setToneWatchList(res.data.stocks || []);
        } catch (err) {
            console.error("Failed to fetch tone watch list", err);
        }
    };

    const handleAddWatchStock = async () => {
        if (!newWatchCode.trim()) return;
        try {
            await axios.post('http://localhost:8000/api/expert/tone-watch/add', {
                user: user,
                code: newWatchCode.trim()
            });
            setNewWatchCode('');
            fetchToneWatchList();
            fetchToneChanges();
        } catch (err) {
            console.error("Failed to add watch stock", err);
        }
    };

    const handleRemoveWatchStock = async (code) => {
        try {
            await axios.post('http://localhost:8000/api/expert/tone-watch/remove', {
                user: user,
                code: code
            });
            fetchToneWatchList();
            fetchToneChanges();
        } catch (err) {
            console.error("Failed to remove watch stock", err);
        }
    };

    const handleViewNews = async (code) => {
        try {
            const res = await axios.get(`http://localhost:8000/api/expert/stock-news/${code}`);
            setSelectedNewsStock(res.data);
            setStockNews(res.data.news || []);
            setKeywordInput('');
            setKeywordSearchResults(null);

            // Fetch saved keywords for this stock
            const kwRes = await axios.get(`http://localhost:8000/api/expert/stock-keywords/${code}?user=${user}`);
            setStockKeywords(kwRes.data.keywords || []);
        } catch (err) {
            console.error("Failed to fetch stock news", err);
        }
    };

    const closeNewsModal = () => {
        setSelectedNewsStock(null);
        setStockNews([]);
        setKeywordInput('');
        setStockKeywords([]);
        setKeywordSearchResults(null);
    };

    const handleSearchKeyword = async () => {
        if (!keywordInput.trim() || !selectedNewsStock) return;

        setSearchingKeyword(true);
        try {
            // Search news with keyword
            const res = await axios.get(
                `http://localhost:8000/api/expert/news/search?keyword=${encodeURIComponent(keywordInput)}&code=${selectedNewsStock.code}`
            );
            setKeywordSearchResults(res.data);

            // Save keyword to user's list
            await axios.post('http://localhost:8000/api/expert/stock-keywords/add', {
                user: user,
                code: selectedNewsStock.code,
                keyword: keywordInput.trim()
            });

            // Refresh saved keywords
            const kwRes = await axios.get(`http://localhost:8000/api/expert/stock-keywords/${selectedNewsStock.code}?user=${user}`);
            setStockKeywords(kwRes.data.keywords || []);
        } catch (err) {
            console.error("Failed to search keyword", err);
        } finally {
            setSearchingKeyword(false);
        }
    };

    const handleRemoveKeyword = async (keyword) => {
        if (!selectedNewsStock) return;

        try {
            await axios.post('http://localhost:8000/api/expert/stock-keywords/remove', {
                user: user,
                code: selectedNewsStock.code,
                keyword: keyword
            });

            // Refresh saved keywords
            const kwRes = await axios.get(`http://localhost:8000/api/expert/stock-keywords/${selectedNewsStock.code}?user=${user}`);
            setStockKeywords(kwRes.data.keywords || []);
        } catch (err) {
            console.error("Failed to remove keyword", err);
        }
    };

    // Filter stocks by search term
    const filteredStocks = stocks.filter(stock =>
        stock.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.code?.includes(searchTerm)
    );

    return (
        <div className="container expert-mode">
            <header className="page-header">
                <h1>시장 심층 분석</h1>
                <p>데이터 기반의 전문적인 인사이트를 제공합니다.</p>
            </header>

            <div className="tabs">
                <button
                    className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                    onClick={() => setActiveTab('all')}
                >
                    전체 종목 시세 <span className="badge">{stocks.length}</span>
                </button>
                <button
                    className={`tab-btn ${activeTab === 'tone' ? 'active' : ''}`}
                    onClick={() => setActiveTab('tone')}
                >
                    톤 변화 감지 <span className="badge badge-negative">{toneChanges.length}</span>
                </button>
            </div>

            {activeTab === 'all' ? (
                <div className="card table-card">
                    <div className="table-header">
                        <h2>전체 종목 시세 ({stocks.length}개)</h2>
                        <input
                            type="text"
                            placeholder="종목명 또는 코드 검색..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                    {loading ? (
                        <div className="loading-container">
                            <p>350개 종목 데이터 로딩 중...</p>
                        </div>
                    ) : (
                        <div className="table-scroll">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>종목코드</th>
                                        <th>종목명</th>
                                        <th>현재가</th>
                                        <th>등락률</th>
                                        <th>52주 고가</th>
                                        <th>52주 저가</th>
                                        <th>섹터</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStocks.map(stock => (
                                        <tr key={stock.code}>
                                            <td>{stock.code}</td>
                                            <td>{stock.name}</td>
                                            <td>{stock.current_price?.toLocaleString()}원</td>
                                            <td className={stock.change_rate >= 0 ? 'positive' : 'negative'}>
                                                {stock.change_rate >= 0 ? '+' : ''}{(stock.change_rate * 100)?.toFixed(2)}%
                                            </td>
                                            <td>{stock.week_52_high?.toLocaleString() || '-'}원</td>
                                            <td>{stock.week_52_low?.toLocaleString() || '-'}원</td>
                                            <td><span className="tag">{stock.sector}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            ) : (
                <div className="tone-analysis-view">
                    {/* Watch List Management */}
                    <div className="card watch-list-card">
                        <h2>📋 관심 종목 관리</h2>
                        <div className="watch-list-header">
                            <input
                                type="text"
                                placeholder="종목코드 입력 (예: 005930)"
                                value={newWatchCode}
                                onChange={(e) => setNewWatchCode(e.target.value)}
                                className="watch-input"
                            />
                            <button className="btn btn-primary" onClick={handleAddWatchStock}>추가</button>
                        </div>
                        <div className="watch-tags">
                            {toneWatchList.map(stock => (
                                <span key={stock.code} className="watch-tag">
                                    {stock.name || stock.code}
                                    <button
                                        className="remove-btn"
                                        onClick={() => handleRemoveWatchStock(stock.code)}
                                    >×</button>
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <h2>📊 톤 변화 분석 결과</h2>
                            <ul className="tone-list">
                                {toneChanges.map((item, idx) => (
                                    <li key={idx} className="tone-item">
                                        <div className="tone-header">
                                            <span className="stock-name">{item.name}</span>
                                            <div className="tone-badges">
                                                <span className={`badge ${item.change === 'Positive' ? 'badge-positive' : item.change === 'Negative' ? 'badge-negative' : 'badge-neutral'}`}>
                                                    {item.change === 'Positive' ? '긍정' : item.change === 'Negative' ? '부정' : '중립'}
                                                </span>
                                                {item.tone_change && item.tone_change !== 'Unknown' && (
                                                    <span className={`badge badge-trend ${item.tone_change === 'Improving' ? 'badge-up' : item.tone_change === 'Declining' ? 'badge-down' : 'badge-maintain'}`}>
                                                        {item.tone_change === 'Improving' ? '↑ 개선' : item.tone_change === 'Declining' ? '↓ 악화' : '→ 유지'}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="tone-stats">
                                            <span>센티먼트 점수: <strong>{(item.sentiment_score * 100).toFixed(0)}점</strong></span>
                                            <span>리포트: <strong>{item.report_count}개</strong></span>
                                        </div>
                                        <p className="tone-reason">{item.reason}</p>
                                        {item.latest_report && (
                                            <p className="tone-latest">
                                                최신: {item.latest_report.date} {item.latest_report.broker} - "{item.latest_report.opinion}"
                                            </p>
                                        )}
                                        <div className="tone-actions">
                                            <button
                                                className="btn btn-sm btn-outline"
                                                onClick={() => handleViewNews(item.code)}
                                            >
                                                📰 리포트/뉴스 보기 ({item.report_count || 0})
                                            </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="card">
                            <h2>📈 센티먼트 점수 비교</h2>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart
                                    data={toneChanges.map(t => ({
                                        name: t.name,
                                        score: Math.round((t.sentiment_score || 0) * 100),
                                        리포트수: t.report_count || 0
                                    }))}
                                    layout="vertical"
                                    margin={{ left: 80, right: 30 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" domain={[-100, 100]} tickFormatter={(v) => `${v}점`} />
                                    <YAxis type="category" dataKey="name" width={70} />
                                    <Tooltip
                                        formatter={(value, name) => [
                                            name === 'score' ? `${value}점` : `${value}개`,
                                            name === 'score' ? '센티먼트' : '리포트 수'
                                        ]}
                                    />
                                    <Legend />
                                    <Bar dataKey="score" name="센티먼트 점수" label={{ position: 'right', formatter: (v) => `${v}점` }}>
                                        {toneChanges.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={(entry.sentiment_score || 0) >= 0 ? '#22c55e' : '#ef4444'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                            <div className="chart-legend">
                                <span className="legend-item"><span className="dot positive"></span> 긍정 (0~100)</span>
                                <span className="legend-item"><span className="dot negative"></span> 부정 (-100~0)</span>
                            </div>
                            <div className="chart-note">
                                * 애널리스트 리포트 텍스트 분석 기반 센티먼트 점수 (-100 ~ +100)
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* News Modal with Keyword Search */}
            {selectedNewsStock && (
                <div className="modal-overlay" onClick={closeNewsModal}>
                    <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>📰 {selectedNewsStock.name} 관련 뉴스</h2>
                            <button className="close-btn" onClick={closeNewsModal}>×</button>
                        </div>
                        <div className="modal-body">
                            {/* Keyword Search Section */}
                            <div className="keyword-search-section">
                                <div className="keyword-input-row">
                                    <input
                                        type="text"
                                        placeholder="키워드 입력 (예: 실적, HBM, AI)"
                                        value={keywordInput}
                                        onChange={(e) => setKeywordInput(e.target.value)}
                                        className="keyword-input"
                                        onKeyPress={(e) => e.key === 'Enter' && handleSearchKeyword()}
                                    />
                                    <button
                                        className="btn btn-primary btn-sm"
                                        onClick={handleSearchKeyword}
                                        disabled={searchingKeyword}
                                    >
                                        {searchingKeyword ? '검색중...' : '🔍 검색'}
                                    </button>
                                </div>
                                {stockKeywords.length > 0 && (
                                    <div className="saved-keywords">
                                        <span className="keyword-label">저장된 키워드:</span>
                                        {stockKeywords.map((kw, idx) => (
                                            <span key={idx} className="keyword-tag">
                                                {kw}
                                                <button
                                                    className="remove-kw-btn"
                                                    onClick={() => handleRemoveKeyword(kw)}
                                                >×</button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Keyword Search Results */}
                            {keywordSearchResults && (
                                <div className="keyword-results">
                                    <h4>🔎 "{keywordSearchResults.keyword}" 검색 결과 ({keywordSearchResults.count}건)</h4>
                                    {keywordSearchResults.news.length > 0 ? (
                                        <ul className="news-list">
                                            {keywordSearchResults.news.map((news, idx) => (
                                                <li key={idx} className="news-item">
                                                    <div className="news-header">
                                                        <span className={`badge ${news.sentiment === 'Positive' ? 'badge-positive' : news.sentiment === 'Negative' ? 'badge-negative' : 'badge-neutral'}`}>
                                                            {news.sentiment}
                                                        </span>
                                                        <span className="news-date">{news.date}</span>
                                                    </div>
                                                    <h3 className="news-title">{news.title}</h3>
                                                    <p className="news-content">{news.content}</p>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="no-news">키워드와 일치하는 뉴스가 없습니다.</p>
                                    )}
                                </div>
                            )}

                            {/* All Related News */}
                            {!keywordSearchResults && (
                                <>
                                    <h4>전체 관련 뉴스</h4>
                                    {stockNews.length > 0 ? (
                                        <ul className="news-list">
                                            {stockNews.map((news, idx) => (
                                                <li key={idx} className="news-item">
                                                    <div className="news-header">
                                                        <span className={`badge ${news.sentiment === 'Positive' ? 'badge-positive' : news.sentiment === 'Negative' ? 'badge-negative' : 'badge-neutral'}`}>
                                                            {news.sentiment}
                                                        </span>
                                                        <span className="news-date">{news.date}</span>
                                                    </div>
                                                    <h3 className="news-title">{news.title}</h3>
                                                    <p className="news-content">{news.content}</p>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="no-news">관련 뉴스가 없습니다.</p>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExpertMode;
