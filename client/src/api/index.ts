import axios from 'axios';
import type {
  PredictRequest,
  PredictResponse,
  ADRRequest,
  ADRResponse,
  SearchResponse
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const searchDrugs = async (q: string): Promise<SearchResponse> => {
  const { data } = await api.get('/drugs/search', { params: { q } });
  return data;
};

export const searchADRDrugs = async (q: string): Promise<SearchResponse> => {
  const { data } = await api.get('/adr/drugs/search', { params: { q } });
  return data;
};

export const predictPolypharmacy = async (req: PredictRequest): Promise<PredictResponse> => {
  const { data } = await api.post('/predict', req);
  return data;
};

export const predictADR = async (req: ADRRequest): Promise<ADRResponse> => {
  const { data } = await api.post('/predict-adr', req);
  return data;
};

export default api;
