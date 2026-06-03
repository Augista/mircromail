import { pgTable, text, timestamp, boolean } from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm'

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  name: text('name'),
  email: text('email').unique().notNull(),
  passwordHash: text('password_hash').notNull(),
  emailVerified: boolean('email_verified').default(false),
  image: text('image'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
})

export const emails = pgTable('emails', {
  id: text('id').primaryKey(),
  userId: text('user_id')
    .notNull()
    .references(() => users.id, { onDelete: 'cascade' }),
  from: text('from').notNull(),
  fromName: text('from_name'),
  to: text('to').notNull(),
  subject: text('subject').notNull(),
  body: text('body').notNull(),
  preview: text('preview'),
  read: boolean('read').default(false),
  archived: boolean('archived').default(false),
  deleted: boolean('deleted').default(false),
  isDraft: boolean('is_draft').default(false),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
})

export const userRelations = relations(users, ({ many }) => ({
  emails: many(emails),
}))

export const emailsRelations = relations(emails, ({ one }) => ({
  user: one(users, {
    fields: [emails.userId],
    references: [users.id],
  }),
}))
