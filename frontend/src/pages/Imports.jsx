import { useState, useEffect } from 'react';
import { getImports } from '../services/api';

export default function Imports() {
  const [imports, setImports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchImports() {
      try {
        const data = await getImports();
        setImports(data.results || data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchImports();
  }, []);

  const formatDate = (date) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Import History</h1>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Filename</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Date</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Imported</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Updated</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Skipped</th>
              <th className="px-6 py-3 text-center font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {imports.map((imp) => (
              <tr key={imp.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <span className="font-medium">{imp.filename}</span>
                  {imp.date_range_start && (
                    <p className="text-xs text-gray-500">
                      {imp.date_range_start} - {imp.date_range_end}
                    </p>
                  )}
                </td>
                <td className="px-6 py-4 text-gray-500">
                  {formatDate(imp.import_date)}
                </td>
                <td className="px-6 py-4 text-right text-green-600 font-medium">
                  {imp.rows_imported}
                </td>
                <td className="px-6 py-4 text-right text-blue-600 font-medium">
                  {imp.rows_updated}
                </td>
                <td className="px-6 py-4 text-right text-gray-500">
                  {imp.rows_skipped}
                </td>
                <td className="px-6 py-4 text-center">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      imp.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : imp.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {imp.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {imports.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No imports found. Use the CSV importer CLI to import data.
          </div>
        )}
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-medium text-blue-900">Import Data via CLI</h3>
        <p className="text-sm text-blue-700 mt-1">
          Use the command line to import CSV files from Meta Business Suite:
        </p>
        <pre className="mt-2 bg-blue-100 p-2 rounded text-sm text-blue-900">
          python csv_importer.py import-all
        </pre>
      </div>
    </div>
  );
}
