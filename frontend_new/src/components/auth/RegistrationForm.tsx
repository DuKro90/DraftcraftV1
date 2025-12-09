/**
 * User Registration Form Component
 */

import React from 'react'
import { useForm } from 'react-hook-form'
import { useRegister } from '@/lib/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import Button from '@/components/ui/Button'
import FormField from '@/components/ui/FormField'
import { UserPlus } from 'lucide-react'

interface RegisterFormData {
  username: string
  email: string
  password: string
  password_confirm: string
}

export const RegistrationForm: React.FC = () => {
  const navigate = useNavigate()
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterFormData>()
  const { mutate: registerUser, isPending, error } = useRegister()

  const password = watch('password')

  const onSubmit = (data: RegisterFormData) => {
    registerUser(data, {
      onSuccess: () => {
        navigate('/documents')
      },
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="text-center mb-8">
        <UserPlus className="h-12 w-12 text-blue-600 mx-auto mb-3" />
        <h2 className="text-2xl font-bold text-gray-900">Account erstellen</h2>
        <p className="text-gray-600 mt-2">Registrieren Sie sich für DraftCraft</p>
      </div>

      <FormField label="Benutzername" error={errors.username?.message}>
        <input
          {...register('username', { required: 'Benutzername ist erforderlich' })}
          type="text"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="benutzername"
        />
      </FormField>

      <FormField label="E-Mail" error={errors.email?.message}>
        <input
          {...register('email', {
            required: 'E-Mail ist erforderlich',
            pattern: { value: /^\S+@\S+$/i, message: 'Ungültige E-Mail' },
          })}
          type="email"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="email@beispiel.de"
        />
      </FormField>

      <FormField label="Passwort" error={errors.password?.message}>
        <input
          {...register('password', {
            required: 'Passwort ist erforderlich',
            minLength: { value: 8, message: 'Mindestens 8 Zeichen' },
          })}
          type="password"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="••••••••"
        />
      </FormField>

      <FormField label="Passwort bestätigen" error={errors.password_confirm?.message}>
        <input
          {...register('password_confirm', {
            required: 'Passwort-Bestätigung ist erforderlich',
            validate: (value) => value === password || 'Passwörter stimmen nicht überein',
          })}
          type="password"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="••••••••"
        />
      </FormField>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error.message}</p>
        </div>
      )}

      <Button type="submit" disabled={isPending} className="w-full">
        {isPending ? 'Erstellt Account...' : 'Registrieren'}
      </Button>

      <p className="text-center text-sm text-gray-600">
        Bereits registriert?{' '}
        <a href="/login" className="text-blue-600 hover:underline">
          Jetzt anmelden
        </a>
      </p>
    </form>
  )
}
