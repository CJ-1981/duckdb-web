import { Page } from '@playwright/test';

/**
 * Test data fixtures for E2E tests
 * Provides CSV test data and upload helpers
 */

export interface TestDataFile {
  name: string;
  content: string;
  filename: string;
}

/**
 * Sample CSV test data
 */
export const sampleCsvData: TestDataFile = {
  name: 'Sample Users',
  content: `id,name,email,age,city
1,Alice Smith,alice@example.com,30,New York
2,Bob Johnson,bob@example.com,25,Los Angeles
3,Carol Davis,carol@example.com,35,Chicago
4,Davis Wilson,davis@example.com,28,Houston
5,Eva Martinez,eva@example.com,32,Phoenix
6,Frank Brown,frank@example.com,27,Philadelphia
7,Grace Lee,grace@example.com,31,San Antonio
8,Henry Taylor,henry@example.com,29,San Diego
9,Ivy White,ivy@example.com,26,Dallas
10,Jack Harris,jack@example.com,33,San Jose`,

  filename: 'sample-users.csv',
};

/**
 * CSV data with null values for testing null handling
 */
export const csvWithNulls: TestDataFile = {
  name: 'Users with Nulls',
  content: `id,name,email,age,city
1,Alice Smith,alice@example.com,30,New York
2,Bob Johnson,,25,Los Angeles
3,Carol Davis,carol@example.com,,Chicago
4,Davis Wilson,davis@example.com,28,
5,Eva Martinez,eva@example.com,32,Phoenix`,

  filename: 'users-with-nulls.csv',
};

/**
 * CSV data with special characters for testing special character handling
 */
export const csvWithSpecialChars: TestDataFile = {
  name: 'Products with Special Chars',
  content: `id,name,description,price
1,Widget A,"Standard widget, with commas",19.99
2,Widget B,"Widget with ""quotes"" inside",29.99
3,Widget C,"Widget
with newlines",39.99
4,Widget D,"Widget/with/slashes",49.99
5,Widget E,"Widget with @ # $ % symbols",59.99`,

  filename: 'products-special-chars.csv',
};

/**
 * CSV data for join operations
 */
export const ordersData: TestDataFile = {
  name: 'Orders',
  content: `order_id,user_id,product,amount
101,1,Widget A,19.99
102,2,Widget B,29.99
103,1,Widget C,39.99
104,3,Widget A,19.99
105,4,Widget D,49.99`,

  filename: 'orders.csv',
};

/**
 * CSV data for aggregation tests
 */
export const salesData: TestDataFile = {
  name: 'Sales Data',
  content: `region,product,sales,quarter
North,Widget A,1000,Q1
North,Widget A,1500,Q2
North,Widget B,800,Q1
South,Widget A,1200,Q1
South,Widget B,900,Q2
East,Widget A,1100,Q1
East,Widget B,1300,Q2
West,Widget A,900,Q1
West,Widget B,1050,Q2`,

  filename: 'sales.csv',
};

/**
 * Create a file input element and upload a test CSV file
 */
export async function uploadTestCsv(page: Page, testData: TestDataFile) {
  // Create a buffer from the CSV content
  // Wait for backend to be ready before uploading
  await page.waitForTimeout(5000);
  const buffer = Buffer.from(testData.content, 'utf-8');

  // Create a temporary file
  const fileChooserPromise = page.waitForEvent('filechooser');
  
  // The input is hidden inside the label, so we might need to click the label or force click the input
  const fileInput = page.locator('input[type="file"]');
  await fileInput.click({ force: true });
  
  const fileChooser = await fileChooserPromise;

  await fileChooser.setFiles({
    name: testData.filename,
    mimeType: 'text/csv',
    buffer: buffer,
  });

  // Wait for upload to complete (frontend shows a success message)
  await page.locator('text=/file uploaded/i').waitFor({ state: 'visible', timeout: 30000 });
}

/**
 * Upload test CSV using drag and drop
 */
export async function dragAndDropCsv(page: Page, testData: TestDataFile) {
  const dropZone = page.locator('[data-testid="drop-zone"], .drop-zone');
  const buffer = Buffer.from(testData.content, 'utf-8');

  // Create a data transfer object with the file
  const dataTransfer = await page.evaluateHandle(({ name, content }) => {
    const dt = new DataTransfer();
    const blob = new Blob([content], { type: 'text/csv' });
    dt.items.add(new File([blob], name, { type: 'text/csv' }));
    return dt;
  }, { name: testData.filename, content: testData.content });

  await dropZone.dispatchEvent('drop', { dataTransfer });
}

/**
 * Get all available test datasets
 */
export function getAllTestDatasets(): TestDataFile[] {
  return [
    sampleCsvData,
    csvWithNulls,
    csvWithSpecialChars,
    ordersData,
    salesData,
  ];
}

/**
 * Get test dataset by name
 */
export function getTestDataset(name: string): TestDataFile | undefined {
  return getAllTestDatasets().find(dataset => dataset.name === name);
}
