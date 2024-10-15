import React, { useState } from 'react';
import axios from 'axios';
import './App.css';  // Import the CSS file

// Reusable SearchResults component to display the results
const SearchResults = ({ queryResultsData }) => {
  console.log(queryResultsData)
  return (
    <div>
      {queryResultsData.length > 0 ? (
        <ul>
          {queryResultsData.map((result, index) => (
            <li key={index}>
              <a href={result.url}>{result.url}</a><br/>
              <strong>Name:</strong> {result.name}<br/>
              <strong>Weighted Similarity:</strong> {result.weighted_similarity}<br/>
              <strong>TLDR:</strong> {result.tldr}<br/>
              <strong>Summary:</strong> {result.summary}<br/>
            </li>
          ))}
        </ul>
      ) : (
        <p>No results found.</p>
      )}
    </div>
  );
};

function App() {
  const [queryResultsData, setQueryResultsData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // States for input parameters
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [scrappingTotalLimit, setScrappingTotalLimit] = useState(10);
  const [reuseIndex, setReuseIndex] = useState(true);

  // States for refinement
  const [positive, setPositive] = useState('');
  const [negative, setNegative] = useState('');

  // Fetch query results (query_results)
  const fetchQueryResults = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('http://127.0.0.1:8000/user/query_results', {
        params: {
          query,
          top_k: topK,
          scrapping_total_limit: scrappingTotalLimit,
          reuse_index: reuseIndex,
        }
      });
      setQueryResultsData(response.data);
    } catch (error) {
      console.error('Error fetching query results:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Refine query results (query_refined)
  const refineQueryResults = async () => {
    try {
      setIsLoading(true);

      // Convert CSV strings into arrays by splitting on ';'
      const positiveTerms = positive.split(';').map(term => term.trim());
      const negativeTerms = negative.split(';').map(term => term.trim());

      // Construct the query parameters in the correct format
      const params = new URLSearchParams({
        top_k: topK.toString(),
        positive: positiveTerms.join('&positive='),  // Repeat the parameter for positive
        negative: negativeTerms.join('&negative='),  // Repeat the parameter for negative
      });

      const response = await axios.get(`http://127.0.0.1:8000/user/query_refined?${params}`);
      setQueryResultsData(response.data);
    } catch (error) {
      console.error('Error fetching refined query results:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1 className="primary-color">Wikipedia API Search</h1>

      {/* Parameter Input Box */}
      <div style={{ marginBottom: '20px' }}>
        <h2 className="primary-color">Search for information on last articles</h2>
        <div>
          <label>
            Query:
            <input 
              type="text" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              placeholder="Enter search query"
            />
          </label>
        </div>
        <div>
          <label>
            Top K:
            <input 
              type="number" 
              value={topK} 
              onChange={(e) => setTopK(e.target.value)} 
              placeholder="Number of results"
            />
          </label>
        </div>
        <div>
          <label>
            Scrapping Total Limit:
            <input 
              type="number" 
              value={scrappingTotalLimit} 
              onChange={(e) => setScrappingTotalLimit(e.target.value)} 
              placeholder="Total articles to scrape"
            />
          </label>
        </div>
        <div>
          <label>
            Reuse Index:
            <input 
              type="checkbox" 
              checked={reuseIndex} 
              onChange={(e) => setReuseIndex(e.target.checked)} 
            />
          </label>
        </div>
      </div>

      {/* Button to call the API method */}
      <button className="secondary-color" onClick={fetchQueryResults}>
        Call Search Method
      </button>

      {/* Refinement section */}
      <div style={{ marginBottom: '20px' }}>
        <h2 className="primary-color">Refine Search</h2>
        <div>
          <label>
            Top K:
            <input 
              type="number" 
              value={topK} 
              onChange={(e) => setTopK(e.target.value)} 
              placeholder="Number of results"
            />
          </label>
        </div>
        <div>
          <label>
            Positive:
            <input 
              type="text" 
              value={positive} 
              onChange={(e) => setPositive(e.target.value)} 
              placeholder="Enter Positive Feedback articles (separated by ;) "
            />
          </label>
        </div>
        <div>
          <label>
            Negative:
            <input 
              type="text" 
              value={negative} 
              onChange={(e) => setNegative(e.target.value)} 
              placeholder="Enter Negative Feedback articles (separated by ;) "
            />
          </label>
        </div>
      </div>

      {/* Button to call the API method */}
      <button className="secondary-color" onClick={refineQueryResults}>
        Call Refine Search Method
      </button>

      <h2 className="primary-color">Results</h2>

      {/* Loading Indicator */}
      {isLoading && <p>Loading...</p>}

      {/* Display Query Results */}
      <SearchResults queryResultsData={queryResultsData} />
    </div>
  );
}

export default App;
