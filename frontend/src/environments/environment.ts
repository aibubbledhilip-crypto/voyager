export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  appName: 'voyager',
  appVersion: '2.0.0',
  defaultAdmin: {
    username: 'admin',
    password: 'admin123'
  },
  maxFileSize: 100 * 1024 * 1024, // 100MB
  maxFiles: 50,
  rateLimit: {
    queriesPerMinute: 10
  },
  athena: {
    maxQueryLength: 10000,
    defaultDownloadLimit: 100000,
    defaultDisplayLimit: 1000
  }
};
