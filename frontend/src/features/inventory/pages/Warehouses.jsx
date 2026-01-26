import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Warehouse, MapPin, Users, Box, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { inventoryAPI } from '../services/inventoryAPI';
import WarehouseForm from '../components/WarehouseForm';

export default function Warehouses() {
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => inventoryAPI.getWarehouses(),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Warehouses</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage storage locations
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Warehouse
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.warehouses?.map((warehouse) => (
            <Link
              key={warehouse.id}
              to={`/inventory/warehouses/${warehouse.id}`}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                  <Warehouse className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  warehouse.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {warehouse.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                {warehouse.name}
              </h3>
              <p className="text-sm text-gray-500 mb-4">Code: {warehouse.code}</p>

              {warehouse.address?.city && (
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                  <MapPin className="w-4 h-4" />
                  {warehouse.address.city}, {warehouse.address.country}
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Box className="w-4 h-4" />
                    {warehouse.zones_count} zones
                  </div>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <MapPin className="w-4 h-4" />
                    {warehouse.locations_count} locations
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {showForm && (
        <WarehouseForm
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false);
            queryClient.invalidateQueries(['warehouses']);
          }}
        />
      )}
    </div>
  );
}
